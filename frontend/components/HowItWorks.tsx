import { Mic, AudioLines, Brain, CalendarCheck, Volume2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type Step = {
  icon: LucideIcon;
  label: string;
  detail: string;
};

const steps: Step[] = [
  { icon: Mic, label: "Caller speaks", detail: "Live mic audio streamed over WebSocket" },
  { icon: AudioLines, label: "Speech-to-text", detail: "Groq Whisper transcribes in real time" },
  { icon: Brain, label: "Intent understood", detail: "LangGraph routes the conversation" },
  { icon: CalendarCheck, label: "Answers or books", detail: "RAG lookup or calendar tool call" },
  { icon: Volume2, label: "Responds by voice", detail: "Deepgram speaks the reply back" },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="scroll-mt-24 px-6 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="reveal max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand">
            How it works
          </p>
          <h2 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
            One conversation, five moves.
          </h2>
        </div>

        <div className="relative mt-16">
          <div className="absolute left-0 right-0 top-6 hidden h-px bg-line lg:block" />
          <ol className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-5 lg:gap-6">
            {steps.map((step, i) => (
              <li
                key={step.label}
                className="reveal relative flex flex-col items-start lg:items-center lg:text-center"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full border border-line bg-surface shadow-sm">
                  <step.icon className="h-5 w-5 text-brand" strokeWidth={1.9} />
                </div>
                <span className="mt-4 font-mono text-xs font-medium text-muted">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-1.5 text-[15px] font-semibold text-ink">
                  {step.label}
                </h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted lg:max-w-[10rem]">
                  {step.detail}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
