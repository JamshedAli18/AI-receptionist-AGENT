import Link from "next/link";
import { ArrowRight, ChevronDown } from "lucide-react";
import VoiceRing from "./VoiceRing";

export default function Hero() {
  return (
    <section className="relative overflow-hidden px-6 pt-20 pb-24 sm:pt-28 sm:pb-32">
      <div
        className="pointer-events-none absolute inset-x-0 -top-40 -z-10 h-[560px] opacity-[0.15] blur-3xl"
        style={{
          background:
            "radial-gradient(60% 60% at 50% 0%, var(--color-brand) 0%, transparent 70%)",
        }}
      />

      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-16 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="reveal">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-live" />
            AI voice receptionist, live 24/7
          </div>

          <h1 className="font-display text-4xl font-extrabold leading-[1.08] tracking-tight text-ink sm:text-5xl lg:text-[3.4rem]">
            Your clinic&apos;s front desk,
            <br />
            <span className="text-brand">automated.</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">
            Recepta answers the phone, books and reschedules appointments,
            and handles patient questions through natural voice
            conversation — day or night, without hold music.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Link
              href="/demo"
              className="group inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-ink/15 transition-all duration-200 hover:shadow-xl hover:shadow-ink/20 hover:-translate-y-0.5"
            >
              Try the Live Demo
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center gap-1.5 rounded-full px-5 py-3.5 text-sm font-semibold text-ink transition-colors duration-200 hover:text-brand"
            >
              See how it works
              <ChevronDown className="h-4 w-4" />
            </a>
          </div>
        </div>

        <div className="reveal" style={{ animationDelay: "0.15s" }}>
          <VoiceRing />
        </div>
      </div>
    </section>
  );
}
