import aiosqlite
import os
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tutor.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db", "schema.sql")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db():
    """Initialize the database with schema."""
    schema = Path(SCHEMA_PATH).read_text()
    db = await get_db()
    try:
        await db.executescript(schema)
        await db.commit()
    finally:
        await db.close()


# --- Session helpers ---

async def create_session(db: aiosqlite.Connection, session_id: str, module_id: str, language: str):
    await db.execute(
        "INSERT INTO sessions (id, module_id, language) VALUES (?, ?, ?)",
        (session_id, module_id, language),
    )
    await db.commit()


async def get_session(db: aiosqlite.Connection, session_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


async def update_session_position(db: aiosqlite.Connection, session_id: str, section: int, step: int):
    await db.execute(
        "UPDATE sessions SET current_section = ?, current_step = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (section, step, session_id),
    )
    await db.commit()


async def update_session_status(db: aiosqlite.Connection, session_id: str, status: str):
    await db.execute(
        "UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, session_id),
    )
    await db.commit()


# --- Section progress helpers ---

async def init_section_progress(db: aiosqlite.Connection, session_id: str, section_count: int):
    for i in range(section_count):
        await db.execute(
            "INSERT OR IGNORE INTO section_progress (session_id, section_index, status) VALUES (?, ?, 'not_started')",
            (session_id, i),
        )
    await db.commit()


async def update_section_progress(db: aiosqlite.Connection, session_id: str, section_index: int, status: str):
    if status == "in_progress":
        await db.execute(
            "UPDATE section_progress SET status = ?, started_at = CURRENT_TIMESTAMP WHERE session_id = ? AND section_index = ?",
            (status, session_id, section_index),
        )
    elif status == "completed":
        await db.execute(
            "UPDATE section_progress SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE session_id = ? AND section_index = ?",
            (status, session_id, section_index),
        )
    else:
        await db.execute(
            "UPDATE section_progress SET status = ? WHERE session_id = ? AND section_index = ?",
            (status, session_id, section_index),
        )
    await db.commit()


async def get_section_progress(db: aiosqlite.Connection, session_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM section_progress WHERE session_id = ? ORDER BY section_index",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# --- Conversation log helpers ---

async def log_conversation(db: aiosqlite.Connection, session_id: str, section_index: int, step_index: int, role: str, text: str, language: str = "en"):
    await db.execute(
        "INSERT INTO conversation_log (session_id, section_index, step_index, role, text, language) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, section_index, step_index, role, text, language),
    )
    await db.commit()


async def get_conversation_history(db: aiosqlite.Connection, session_id: str, section_index: int | None = None) -> list[dict]:
    if section_index is not None:
        cursor = await db.execute(
            "SELECT role, text FROM conversation_log WHERE session_id = ? AND section_index = ? ORDER BY id",
            (session_id, section_index),
        )
    else:
        cursor = await db.execute(
            "SELECT role, text FROM conversation_log WHERE session_id = ? ORDER BY id",
            (session_id,),
        )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
