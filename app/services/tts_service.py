import httpx
from app.config import DEEPGRAM_API_KEY, DEEPGRAM_TTS_MODEL

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"


async def synthesize_speech(text: str) -> bytes:
    """
    Converts text to speech using Deepgram Aura-2, returns raw audio bytes
    (mp3 by default). Async since this runs inside the FastAPI WebSocket
    handler's event loop.
    """
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {"model": DEEPGRAM_TTS_MODEL, "encoding": "mp3"}
    body = {"text": text}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(DEEPGRAM_TTS_URL, headers=headers, params=params, json=body)
        response.raise_for_status()
        return response.content