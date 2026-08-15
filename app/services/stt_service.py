import io
from app.config import groq_client, WHISPER_MODEL


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribes raw audio bytes using Groq's whisper-large-v3-turbo.
    Accepts webm/opus (what MediaRecorder produces in the browser) directly —
    Groq's Whisper endpoint handles common container formats natively.
    """
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename  # Groq's SDK reads this for the multipart filename

    transcription = groq_client.audio.transcriptions.create(
        file=audio_file,
        model=WHISPER_MODEL,
        response_format="text",
    )
    return str(transcription).strip()