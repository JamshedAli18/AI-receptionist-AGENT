from fastapi import FastAPI
from app.routes import voice

app = FastAPI(title="BrightPath Clinic Voice Receptionist")

app.include_router(voice.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "voice-receptionist"}