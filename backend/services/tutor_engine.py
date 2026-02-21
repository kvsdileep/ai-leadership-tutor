"""Tutor engine: state machine that drives the conversation through curriculum steps."""

import json
from pathlib import Path
from backend.services.gemini import generate_tutor_response

CURRICULUM_DIR = Path(__file__).parent.parent / "curriculum"

_curriculum_cache: dict = {}


def load_curriculum(module_id: str) -> dict:
    if module_id not in _curriculum_cache:
        path = CURRICULUM_DIR / f"{module_id}.json"
        _curriculum_cache[module_id] = json.loads(path.read_text())
    return _curriculum_cache[module_id]


def get_step(curriculum: dict, section_index: int, step_index: int) -> dict | None:
    sections = curriculum["sections"]
    if section_index >= len(sections):
        return None
    section = sections[section_index]
    if step_index >= len(section["steps"]):
        return None
    return section["steps"][step_index]


def get_section(curriculum: dict, section_index: int) -> dict | None:
    sections = curriculum["sections"]
    if section_index >= len(sections):
        return None
    return sections[section_index]


def is_last_step(curriculum: dict, section_index: int, step_index: int) -> bool:
    section = get_section(curriculum, section_index)
    if section is None:
        return True
    return step_index >= len(section["steps"]) - 1


def is_last_section(curriculum: dict, section_index: int) -> bool:
    return section_index >= len(curriculum["sections"]) - 1


def next_position(curriculum: dict, section_index: int, step_index: int) -> tuple[int, int]:
    """Return the next (section_index, step_index), or same position if at end."""
    section = get_section(curriculum, section_index)
    if section is None:
        return section_index, step_index

    if step_index < len(section["steps"]) - 1:
        return section_index, step_index + 1
    elif section_index < len(curriculum["sections"]) - 1:
        return section_index + 1, 0
    else:
        return section_index, step_index  # at the very end


def step_expects_response(step: dict) -> bool:
    """Whether this step type requires learner input before advancing."""
    return step["type"] in ("teach_and_ask", "reflect", "scenario")


def build_system_prompt(curriculum: dict, language: str) -> str:
    lang_name = "Hindi" if language == "hi" else "English"
    return f"""You are a warm, direct leadership tutor in a voice conversation.

Rules:
- Speak in {lang_name}. Maximum 1-2 sentences per turn. Never more than 2.
- This is spoken aloud — be crisp, not wordy.
- No bullet points, lists, or markdown. No filler praise like "Great question!"
- Be specific when affirming. Be genuinely curious when asking.
- Module: {curriculum['title']}"""


async def generate_tutor_turn(
    curriculum: dict,
    section_index: int,
    step_index: int,
    language: str,
    conversation_history: list[dict],
    learner_response: str | None = None,
) -> str:
    """Generate the tutor's next spoken turn based on current curriculum position."""
    step = get_step(curriculum, section_index, step_index)
    if step is None:
        return "Thank you for completing this session. Great work today!"

    system_prompt = build_system_prompt(curriculum, language)

    # Choose the right guidance based on language
    guidance_key = "prompt_guidance_hi" if language == "hi" else "prompt_guidance"
    guidance = step.get(guidance_key, step.get("prompt_guidance", ""))

    # If this is a feedback turn (learner just responded to a teach_and_ask/reflect/scenario)
    if learner_response and "feedback_guidance" in step:
        feedback_key = "feedback_guidance"
        instruction = f"The learner just said: \"{learner_response}\"\n\nYour guidance for responding: {step[feedback_key]}"
    else:
        instruction = f"Your guidance for this turn: {guidance}"

    messages = conversation_history + [{"role": "user", "content": f"[TUTOR INSTRUCTION — not visible to learner]: {instruction}"}]

    return await generate_tutor_response(system_prompt, messages)
