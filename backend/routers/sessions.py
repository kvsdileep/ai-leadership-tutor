import uuid
from fastapi import APIRouter, HTTPException
from backend.models import (
    SessionCreate, SessionResponse, ProgressResponse,
    SectionProgressResponse, SessionStatus, SectionStatus, Language,
)
from backend.database import (
    get_db, create_session, get_session, init_section_progress,
    get_section_progress,
)
from backend.services.tutor_engine import load_curriculum

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def start_session(body: SessionCreate):
    curriculum = load_curriculum(body.module_id)
    session_id = uuid.uuid4().hex[:12]

    db = await get_db()
    try:
        await create_session(db, session_id, body.module_id, body.language.value)
        await init_section_progress(db, session_id, len(curriculum["sections"]))
    finally:
        await db.close()

    return SessionResponse(
        id=session_id,
        module_id=body.module_id,
        language=body.language,
        current_section=0,
        current_step=0,
        status=SessionStatus.active,
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions(status: str | None = None):
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC", (status,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE status IN ('active', 'paused') ORDER BY updated_at DESC"
            )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    return [
        SessionResponse(
            id=r["id"], module_id=r["module_id"], language=Language(r["language"]),
            current_section=r["current_section"], current_step=r["current_step"],
            status=SessionStatus(r["status"]),
        ) for r in rows
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_info(session_id: str):
    db = await get_db()
    try:
        session = await get_session(db, session_id)
    finally:
        await db.close()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=session["id"],
        module_id=session["module_id"],
        language=Language(session["language"]),
        current_section=session["current_section"],
        current_step=session["current_step"],
        status=SessionStatus(session["status"]),
    )


@router.get("/{session_id}/progress", response_model=ProgressResponse)
async def get_progress(session_id: str):
    db = await get_db()
    try:
        session = await get_session(db, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        curriculum = load_curriculum(session["module_id"])
        progress_rows = await get_section_progress(db, session_id)
    finally:
        await db.close()

    sections = []
    for row in progress_rows:
        section_data = curriculum["sections"][row["section_index"]]
        sections.append(SectionProgressResponse(
            section_id=row["section_index"],
            title=section_data["title"],
            status=SectionStatus(row["status"]),
        ))

    return ProgressResponse(
        session_id=session_id,
        module_id=session["module_id"],
        sections=sections,
        overall_status=SessionStatus(session["status"]),
    )
