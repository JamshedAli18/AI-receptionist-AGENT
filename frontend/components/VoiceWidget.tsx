"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, User, AlertCircle } from "lucide-react";

type Turn = { role: "user" | "assistant" | "system"; text: string };

const MAX_RECORDING_MS = 15000;

export default function VoiceWidget() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordStartRef = useRef(0);
  const maxDurationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stoppingRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll the transcript to the latest message, like a modern chat UI.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [turns, processing]);

  function addTurn(role: Turn["role"], text: string) {
    setTurns((prev) => [...prev, { role, text }]);
  }

  function ensureConnected() {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/voice`);
    ws.binaryType = "arraybuffer";

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = async (event: MessageEvent) => {
      if (typeof event.data === "string") {
        if (event.data.startsWith("TRANSCRIPT_USER:")) {
          addTurn("user", event.data.slice("TRANSCRIPT_USER:".length));
        } else if (event.data.startsWith("TRANSCRIPT_ASSISTANT:")) {
          addTurn("assistant", event.data.slice("TRANSCRIPT_ASSISTANT:".length));
        } else if (event.data.startsWith("ERROR:")) {
          addTurn("system", event.data.slice("ERROR:".length));
          setProcessing(false);
        }
        return;
      }
      const blob = new Blob([event.data], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => setProcessing(false);
      audio.play().catch(() => setProcessing(false));
    };

    wsRef.current = ws;
  }

  async function startRecording() {
    // Guard against a second recording starting before the previous one's
    // MediaRecorder and stream tracks have fully released — overlapping
    // instances can interleave audio chunks and corrupt the buffer.
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      return;
    }

    stoppingRef.current = false;
    ensureConnected();

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send("RESET");
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
    mediaRecorderRef.current = mediaRecorder;
    recordStartRef.current = performance.now();

    mediaRecorder.ondataavailable = async (e: BlobEvent) => {
      if (e.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
        const buffer = await e.data.arrayBuffer();
        wsRef.current.send(buffer);
      }
    };

    mediaRecorder.start(100);
    setRecording(true);

    maxDurationTimerRef.current = setTimeout(stopRecording, MAX_RECORDING_MS);
  }

  function stopRecording() {
    if (stoppingRef.current) return;
    stoppingRef.current = true;
    setRecording(false); // disable the button visually immediately

    if (maxDurationTimerRef.current) {
      clearTimeout(maxDurationTimerRef.current);
      maxDurationTimerRef.current = null;
    }

    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder || mediaRecorder.state !== "recording") {
      setRecording(false);
      return;
    }

    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach((t) => t.stop());
    setRecording(false);

    const recordedMs = performance.now() - recordStartRef.current;
    if (recordedMs < 400) return;

    setProcessing(true);
    setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("END");
      }
    }, 200);
  }

  function handlePointerDown(e: React.PointerEvent<HTMLButtonElement>) {
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    startRecording();
  }
  function handlePointerUp(e: React.PointerEvent<HTMLButtonElement>) {
    (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    stopRecording();
  }
  function handlePointerCancel() {
    stopRecording();
  }

  return (
    <div className="w-full max-w-xl mx-auto">
      <div className="bg-surface rounded-[28px] shadow-xl shadow-ink/10 border border-line overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-line flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-6l-4 4v-4z" />
            </svg>
            <h1 className="text-sm font-semibold text-ink leading-tight">Conversation</h1>
          </div>
          <div className="flex items-center gap-1.5 bg-paper rounded-full px-2.5 py-1">
            <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-live" : "bg-line"}`} />
            <span className="text-[11px] font-medium text-muted">
              {connected ? "Live" : "Offline"}
            </span>
          </div>
        </div>

        {/* Conversation */}
        <div
          ref={scrollRef}
          className="no-scrollbar h-96 overflow-y-auto scroll-smooth px-6 py-5 space-y-4 bg-gradient-to-b from-surface to-paper/60"
        >
          {turns.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center gap-2">
              <div className="w-12 h-12 rounded-full bg-paper flex items-center justify-center mb-1">
                <svg className="w-5 h-5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-6l-4 4v-4z" />
                </svg>
              </div>
              <p className="text-sm text-muted">Hold the button below to start talking</p>
            </div>
          ) : (
            turns.map((turn, i) => (
              <div
                key={i}
                className={`reveal flex ${turn.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {turn.role === "system" ? (
                  <div className="mx-auto flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1.5 text-[11px] font-medium text-red-500">
                    <AlertCircle className="h-3 w-3 shrink-0" strokeWidth={2.25} />
                    {turn.text}
                  </div>
                ) : (
                  <div
                    className={`flex items-end gap-2 max-w-[85%] ${turn.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                  >
                    <div
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${turn.role === "user" ? "bg-ink" : "bg-brand/10"
                        }`}
                    >
                      {turn.role === "user" ? (
                        <User className="h-3.5 w-3.5 text-white" strokeWidth={2} />
                      ) : (
                        <Bot className="h-3.5 w-3.5 text-brand" strokeWidth={2} />
                      )}
                    </div>
                    <div
                      className={`px-4 py-2.5 text-sm leading-relaxed rounded-2xl ${turn.role === "user"
                          ? "bg-gradient-to-br from-ink to-[#1c1f3d] text-white rounded-br-md shadow-md shadow-ink/20"
                          : "bg-surface border border-line text-ink rounded-bl-md shadow-sm"
                        }`}
                    >
                      {turn.text}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
          {processing && (
            <div className="reveal flex items-end gap-2">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand/10">
                <Bot className="h-3.5 w-3.5 text-brand" strokeWidth={2} />
              </div>
              <div className="bg-surface border border-line rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-line animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-line animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-line animate-bounce" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Mic control */}
        <div className="px-6 py-6 border-t border-line flex flex-col items-center bg-surface">
          <button
            type="button"
            disabled={!connected || processing}
            className={`relative w-16 h-16 rounded-full flex items-center justify-center select-none touch-none transition-all duration-200 disabled:opacity-40 ${recording
                ? "bg-red-500 shadow-lg shadow-red-200 scale-110"
                : "bg-ink hover:bg-brand shadow-md hover:shadow-lg"
              }`}
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerCancel}
            onLostPointerCapture={handlePointerCancel}
          >
            {recording && (
              <span className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-40 pointer-events-none" />
            )}
            <svg className="relative w-6 h-6 text-white pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
            </svg>
          </button>
          <p className="mt-3 text-xs font-medium text-muted">
            {recording ? "Listening…" : processing ? "Thinking…" : "Hold to talk"}
          </p>
        </div>
      </div>
    </div>
  );
}
