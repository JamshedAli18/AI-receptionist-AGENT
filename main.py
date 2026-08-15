from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import ws_voice

app = FastAPI(title="BrightPath Clinic Voice Receptionist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # "*" temporarily, tighten once you have your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_voice.router)
from app.routes import admin
app.include_router(admin.router)