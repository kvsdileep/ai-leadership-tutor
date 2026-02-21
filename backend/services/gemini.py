import httpx
from backend.config import settings


async def chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 150) -> str:
    """Send a chat completion request to Gemini via OpenRouter."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.gemini_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def generate_tutor_response(
    system_prompt: str,
    conversation_history: list[dict],
    temperature: float = 0.7,
) -> str:
    """Generate a tutor response given system prompt and conversation history."""
    messages = [{"role": "system", "content": system_prompt}] + conversation_history
    return await chat_completion(messages, temperature=temperature)
