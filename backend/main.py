from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routers import modules, sessions, conversation
from backend.services.gemini import chat_completion
from backend.services.sarvam_tts import text_to_speech
from backend.services.sarvam_stt import speech_to_text


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="AI Leadership Tutor", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(modules.router)
app.include_router(sessions.router)
app.include_router(conversation.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Dev-only test routes
@app.get("/api/test/gemini")
async def test_gemini():
    result = await chat_completion(
        [{"role": "user", "content": "Say hello in one sentence."}],
        max_tokens=50,
    )
    return {"response": result}


@app.get("/api/test/tts")
async def test_tts():
    audio = await text_to_speech("Hello, welcome to the leadership tutor.", "en")
    return {"audio_base64_length": len(audio)}


@app.post("/api/test/stt")
async def test_stt():
    return {"message": "POST audio file to this endpoint to test STT"}
