import httpx
from backend.config import settings


LANGUAGE_CONFIG = {
    "en": {"language_code": "en-IN"},
    "hi": {"language_code": "hi-IN"},
}


async def text_to_speech(text: str, language: str = "en") -> str:
    """Convert text to speech using Sarvam AI. Returns base64 encoded audio."""
    config = LANGUAGE_CONFIG.get(language, LANGUAGE_CONFIG["en"])

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.sarvam_base_url}/text-to-speech",
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "target_language_code": config["language_code"],
                "model": "bulbul:v2",
                "speaker": "anushka",
            },
        )
        response.raise_for_status()
        data = response.json()
        # Sarvam returns base64-encoded audio in audios array
        return data["audios"][0]
