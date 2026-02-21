import httpx
from backend.config import settings


LANGUAGE_CODE_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
}


async def speech_to_text(audio_bytes: bytes, language: str = "en") -> str:
    """Convert speech to text using Sarvam AI. Accepts raw audio bytes (WAV/WebM)."""
    language_code = LANGUAGE_CODE_MAP.get(language, "en-IN")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.sarvam_base_url}/speech-to-text",
            headers={
                "api-subscription-key": settings.sarvam_api_key,
            },
            files={
                "file": ("audio.webm", audio_bytes, "audio/webm"),
            },
            data={
                "language_code": language_code,
                "model": "saarika:v2.5",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["transcript"]
