from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Language(str, Enum):
    en = "en"
    hi = "hi"


class SessionStatus(str, Enum):
    active = "active"
    completed = "completed"
    paused = "paused"


class SectionStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class SessionCreate(BaseModel):
    module_id: str
    language: Language = Language.en


class SessionResponse(BaseModel):
    id: str
    module_id: str
    language: Language
    current_section: int
    current_step: int
    status: SessionStatus


class ModuleResponse(BaseModel):
    id: str
    title: str
    title_hi: str
    description: str
    section_count: int
    estimated_minutes: int


class SectionProgressResponse(BaseModel):
    section_id: int
    title: str
    status: SectionStatus


class ProgressResponse(BaseModel):
    session_id: str
    module_id: str
    sections: list[SectionProgressResponse]
    overall_status: SessionStatus


# WebSocket message types
class WSMessageType(str, Enum):
    # Client -> Server
    audio = "audio"           # Learner's recorded audio
    skip = "skip"             # Skip current step
    start = "start"           # Start/resume the lesson

    # Server -> Client
    tutor_audio = "tutor_audio"
    tutor_text = "tutor_text"
    learner_text = "learner_text"  # STT transcript of learner
    status = "status"
    progress = "progress"
    error = "error"
    section_complete = "section_complete"
    module_complete = "module_complete"


class WSMessage(BaseModel):
    type: WSMessageType
    data: Optional[dict] = None
