CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    current_section INTEGER NOT NULL DEFAULT 0,
    current_step INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS section_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    section_index INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(session_id, section_index)
);

CREATE TABLE IF NOT EXISTS conversation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    section_index INTEGER NOT NULL,
    step_index INTEGER NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
