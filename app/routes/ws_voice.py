import time
import uuid
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.stt_service import transcribe_audio
from app.services.tts_service import synthesize_speech
from app.graph.graph_builder import receptionist_graph
from app.graph.nodes.greeting_node import greeting_node

router = APIRouter()


async def run_graph(call_sid: str, message: str) -> str:
    """
    receptionist_graph.invoke(...) is synchronous and does blocking network
    calls (Groq, Cohere, Google Calendar, MongoDB) — running it directly in
    the WebSocket's async handler would freeze the event loop for every
    other connection. asyncio.to_thread offloads it to a worker thread.
    """
    config = {"configurable": {"thread_id": call_sid}}

    def _invoke():
        return receptionist_graph.invoke(
            {"current_message": message, "call_sid": call_sid},
            config=config,
        )

    result = await asyncio.to_thread(_invoke)
    return result.get("response_text", "I'm sorry, I didn't catch that.")


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    call_sid = str(uuid.uuid4())
    print(f"[ws] Client connected — call_sid: {call_sid}")

    audio_buffer = bytearray()

    try:
        # Greet the caller immediately, same as a real phone call would
        greeting = greeting_node({})
        greeting_text = greeting["response_text"]
        await websocket.send_text(f"TRANSCRIPT_ASSISTANT:{greeting_text}")

        greeting_audio = await synthesize_speech(greeting_text)
        await websocket.send_bytes(greeting_audio)

        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            if "bytes" in message and message["bytes"] is not None:
                audio_buffer.extend(message["bytes"])
                continue

            if "text" in message:
                text_msg = message["text"]

                if text_msg == "RESET":
                    audio_buffer.clear()
                    continue

                if text_msg == "END":
                    if not audio_buffer:
                        continue

                    t0 = time.perf_counter()
                    audio_bytes = bytes(audio_buffer)
                    audio_buffer.clear()

                    try:
                        stt_start = time.perf_counter()
                        transcript = transcribe_audio(audio_bytes)
                        stt_ms = (time.perf_counter() - stt_start) * 1000
                        print(f"[ws] STT: '{transcript}' ({stt_ms:.0f}ms)")

                        # Filter out trivial STT artifacts — Whisper sometimes
                        # transcribes silence/noise as just "." or similar,
                        # which should never be treated as a real answer.
                        meaningful = transcript.strip().strip(".!?,")
                        if not meaningful or len(meaningful) < 2:
                            await websocket.send_text("ERROR:No speech detected — please try again")
                            continue

                        await websocket.send_text(f"TRANSCRIPT_USER:{transcript}")

                        graph_start = time.perf_counter()
                        response_text = await run_graph(call_sid, transcript)
                        graph_ms = (time.perf_counter() - graph_start) * 1000
                        print(f"[ws] Graph response: '{response_text}' ({graph_ms:.0f}ms)")

                        await websocket.send_text(f"TRANSCRIPT_ASSISTANT:{response_text}")

                        tts_start = time.perf_counter()
                        audio_response = await synthesize_speech(response_text)
                        tts_ms = (time.perf_counter() - tts_start) * 1000
                        print(f"[ws] TTS generated {len(audio_response)} bytes ({tts_ms:.0f}ms)")

                        await websocket.send_bytes(audio_response)

                        total_ms = (time.perf_counter() - t0) * 1000
                        print(
                            f"[ws] Total round trip: {total_ms:.0f}ms "
                            f"(STT {stt_ms:.0f}ms + Graph {graph_ms:.0f}ms + TTS {tts_ms:.0f}ms)"
                        )

                    except Exception as e:
                        print(f"[ws] Processing error: {e}")
                        await websocket.send_text("ERROR:Sorry, I had trouble processing that — please try again")

    except WebSocketDisconnect:
        print(f"[ws] Client disconnected — call_sid: {call_sid}")