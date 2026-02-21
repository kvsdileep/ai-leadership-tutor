"""WebSocket handler for the voice conversation loop."""

import json
import base64
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.database import (
    get_db, get_session, update_session_position, update_session_status,
    update_section_progress, log_conversation, get_conversation_history,
)
from backend.services.tutor_engine import (
    load_curriculum, get_step, get_section, step_expects_response,
    next_position, is_last_step, is_last_section, generate_tutor_turn,
)
from backend.services.sarvam_tts import text_to_speech
from backend.services.sarvam_stt import speech_to_text

logger = logging.getLogger(__name__)
router = APIRouter()


async def send_json(ws: WebSocket, msg_type: str, data: dict | None = None):
    await ws.send_text(json.dumps({"type": msg_type, "data": data or {}}))


async def send_tutor_message(ws: WebSocket, text: str, language: str, pace: float = 1.25):
    """Send tutor text + audio to the client."""
    await send_json(ws, "tutor_text", {"text": text})
    await send_json(ws, "status", {"state": "synthesizing"})
    try:
        audio_b64 = await text_to_speech(text, language, pace=pace)
        await send_json(ws, "tutor_audio", {"audio": audio_b64})
    except Exception as e:
        logger.error(f"TTS error: {e}")
        # Still usable without audio — text was already sent
        await send_json(ws, "error", {"message": "Audio synthesis failed, but you can read the transcript above."})


@router.websocket("/ws/conversation/{session_id}")
async def conversation_ws(ws: WebSocket, session_id: str):
    await ws.accept()

    db = await get_db()
    try:
        session = await get_session(db, session_id)
        if session is None:
            await send_json(ws, "error", {"message": "Session not found"})
            await ws.close()
            return

        module_id = session["module_id"]
        language = session["language"]
        curriculum = load_curriculum(module_id)
        section_idx = session["current_section"]
        step_idx = session["current_step"]
        session_pace = 1.25  # default, updated by client via set_pace message

        # Wait for "start" message from client
        start_msg = await ws.receive_text()
        start_data = json.loads(start_msg)
        if start_data.get("type") != "start":
            await send_json(ws, "error", {"message": "Expected 'start' message"})
            await ws.close()
            return

        # Mark first section as in_progress
        await update_section_progress(db, session_id, section_idx, "in_progress")

        # Reactivate if resuming a paused session
        if session["status"] == "paused":
            await update_session_status(db, session_id, "active")

        # Send initial position info
        section_data = get_section(curriculum, section_idx)
        await send_json(ws, "progress", {
            "section_index": section_idx,
            "step_index": step_idx,
            "section_title": section_data["title"] if section_data else "",
            "total_sections": len(curriculum["sections"]),
        })

        # Send curriculum structure for sidebar
        sections_info = []
        for i, sec in enumerate(curriculum["sections"]):
            sections_info.append({
                "index": i,
                "title": sec["title"],
                "title_hi": sec.get("title_hi", sec["title"]),
                "step_count": len(sec["steps"]),
            })
        await send_json(ws, "curriculum_info", {"sections": sections_info})

        # Generate and send the first tutor turn
        await send_json(ws, "status", {"state": "thinking"})
        history = await _build_gemini_history(db, session_id, section_idx)
        tutor_text = await generate_tutor_turn(curriculum, section_idx, step_idx, language, history)

        await log_conversation(db, session_id, section_idx, step_idx, "tutor", tutor_text, language)
        await send_tutor_message(ws, tutor_text, language, pace=session_pace)

        step = get_step(curriculum, section_idx, step_idx)
        if step and not step_expects_response(step):
            # Auto-advance for teach-only steps
            section_idx, step_idx = _advance(curriculum, db, session_id, section_idx, step_idx)
            await update_session_position(db, session_id, section_idx, step_idx)
            # Generate the next turn immediately
            await _send_next_tutor_turn(ws, db, session_id, curriculum, section_idx, step_idx, language, pace=session_pace)
        else:
            await send_json(ws, "status", {"state": "listening"})

        # Main conversation loop
        while True:
            try:
                raw = await ws.receive()
            except WebSocketDisconnect:
                break

            if "text" in raw:
                msg = json.loads(raw["text"])
            elif "bytes" in raw:
                # Binary audio data
                msg = {"type": "audio", "data": {"audio_bytes": raw["bytes"]}}
            else:
                continue

            msg_type = msg.get("type")

            if msg_type == "audio":
                # Process learner's voice
                await send_json(ws, "status", {"state": "transcribing"})

                audio_data = msg.get("data", {})
                if "audio_bytes" in audio_data:
                    audio_bytes = audio_data["audio_bytes"]
                elif "audio" in audio_data:
                    audio_bytes = base64.b64decode(audio_data["audio"])
                else:
                    await send_json(ws, "error", {"message": "No audio data received"})
                    continue

                try:
                    transcript = await speech_to_text(audio_bytes, language)
                except Exception as e:
                    logger.error(f"STT error: {e}")
                    await send_json(ws, "error", {"message": "Could not understand audio. Please try again."})
                    await send_json(ws, "status", {"state": "listening"})
                    continue

                await send_json(ws, "learner_text", {"text": transcript})
                await log_conversation(db, session_id, section_idx, step_idx, "learner", transcript, language)

                # Generate tutor feedback on learner's response
                await send_json(ws, "status", {"state": "thinking"})
                history = await _build_gemini_history(db, session_id, section_idx)
                feedback_text = await generate_tutor_turn(
                    curriculum, section_idx, step_idx, language, history, learner_response=transcript
                )
                await log_conversation(db, session_id, section_idx, step_idx, "tutor", feedback_text, language)
                await send_tutor_message(ws, feedback_text, language, pace=session_pace)

                # Advance after feedback
                section_idx, step_idx = await _advance_and_notify(
                    ws, db, session_id, curriculum, section_idx, step_idx, language, pace=session_pace
                )

            elif msg_type == "skip":
                # Skip current step
                section_idx, step_idx = await _advance_and_notify(
                    ws, db, session_id, curriculum, section_idx, step_idx, language, pace=session_pace
                )

            elif msg_type == "set_pace":
                pace_val = msg.get("data", {}).get("pace", 1.25)
                session_pace = max(0.5, min(2.0, float(pace_val)))

            elif msg_type == "pause":
                await update_session_status(db, session_id, "paused")
                await send_json(ws, "status", {"state": "paused"})
                await ws.close()
                break

    except WebSocketDisconnect:
        logger.info(f"Session {session_id} disconnected")
    except Exception as e:
        logger.error(f"Conversation error: {e}", exc_info=True)
        try:
            await send_json(ws, "error", {"message": str(e)})
        except Exception:
            pass
    finally:
        await db.close()


def _advance(curriculum: dict, db, session_id: str, section_idx: int, step_idx: int) -> tuple[int, int]:
    """Calculate next position (pure logic, no DB writes)."""
    return next_position(curriculum, section_idx, step_idx)


async def _advance_and_notify(
    ws: WebSocket, db, session_id: str, curriculum: dict,
    section_idx: int, step_idx: int, language: str, pace: float = 1.25
) -> tuple[int, int]:
    """Advance to next step, handle section/module completion, send next tutor turn."""
    old_section = section_idx
    new_section, new_step = next_position(curriculum, section_idx, step_idx)

    if new_section == section_idx and new_step == step_idx:
        # At the very end of the module
        await update_section_progress(db, session_id, section_idx, "completed")
        await update_session_status(db, session_id, "completed")
        await send_json(ws, "module_complete", {"message": "Congratulations! You've completed the module."})
        return new_section, new_step

    if new_section != old_section:
        # Section changed
        await update_section_progress(db, session_id, old_section, "completed")
        await send_json(ws, "section_complete", {
            "section_index": old_section,
            "section_title": get_section(curriculum, old_section)["title"],
        })
        await update_section_progress(db, session_id, new_section, "in_progress")

    await update_session_position(db, session_id, new_section, new_step)

    # Send progress update
    section_data = get_section(curriculum, new_section)
    await send_json(ws, "progress", {
        "section_index": new_section,
        "step_index": new_step,
        "section_title": section_data["title"] if section_data else "",
        "total_sections": len(curriculum["sections"]),
    })

    # Generate next tutor turn
    await _send_next_tutor_turn(ws, db, session_id, curriculum, new_section, new_step, language, pace=pace)
    return new_section, new_step


async def _send_next_tutor_turn(
    ws: WebSocket, db, session_id: str, curriculum: dict,
    section_idx: int, step_idx: int, language: str, pace: float = 1.25
):
    """Generate and send the next tutor turn, then auto-advance if it's teach-only."""
    step = get_step(curriculum, section_idx, step_idx)
    if step is None:
        return

    await send_json(ws, "status", {"state": "thinking"})
    history = await _build_gemini_history(db, session_id, section_idx)
    tutor_text = await generate_tutor_turn(curriculum, section_idx, step_idx, language, history)
    await log_conversation(db, session_id, section_idx, step_idx, "tutor", tutor_text, language)
    await send_tutor_message(ws, tutor_text, language, pace=pace)

    if not step_expects_response(step):
        # Auto-advance for teach-only and summarize steps
        new_section, new_step = next_position(curriculum, section_idx, step_idx)
        if new_section != section_idx or new_step != step_idx:
            await update_session_position(db, session_id, new_section, new_step)

            if new_section != section_idx:
                await update_section_progress(db, session_id, section_idx, "completed")
                await send_json(ws, "section_complete", {
                    "section_index": section_idx,
                    "section_title": get_section(curriculum, section_idx)["title"],
                })
                await update_section_progress(db, session_id, new_section, "in_progress")

            section_data = get_section(curriculum, new_section)
            await send_json(ws, "progress", {
                "section_index": new_section,
                "step_index": new_step,
                "section_title": section_data["title"] if section_data else "",
                "total_sections": len(curriculum["sections"]),
            })
            await _send_next_tutor_turn(ws, db, session_id, curriculum, new_section, new_step, language, pace=pace)
        else:
            # End of module on a teach/summarize step
            await update_section_progress(db, session_id, section_idx, "completed")
            await update_session_status(db, session_id, "completed")
            await send_json(ws, "module_complete", {"message": "Congratulations! You've completed the module."})
    else:
        await send_json(ws, "status", {"state": "listening"})


async def _build_gemini_history(db, session_id: str, section_idx: int) -> list[dict]:
    """Build Gemini-compatible message history from conversation log."""
    rows = await get_conversation_history(db, session_id, section_idx)
    messages = []
    for row in rows:
        role = "assistant" if row["role"] == "tutor" else "user"
        messages.append({"role": role, "content": row["text"]})
    return messages
