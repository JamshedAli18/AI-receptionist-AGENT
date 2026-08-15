import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function DemoCTA() {
  return (
    <section className="px-6 pb-24 sm:pb-32">
      <div className="reveal mx-auto max-w-6xl overflow-hidden rounded-3xl bg-ink px-8 py-16 text-center sm:px-16">
        <div
          className="pointer-events-none relative -mt-32 mb-[-4rem] h-64 opacity-40 blur-3xl"
          style={{
            background:
              "radial-gradient(50% 50% at 50% 50%, var(--color-brand) 0%, transparent 70%)",
          }}
        />
        <h2 className="relative font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
          Talk to it right now.
        </h2>
        <p className="relative mx-auto mt-4 max-w-md text-[15px] leading-relaxed text-white/60">
          No signup, no download — hold the mic button and have a real
          conversation with the receptionist.
        </p>
        <Link
          href="/demo"
          className="group relative mt-8 inline-flex items-center gap-2 rounded-full bg-white px-7 py-3.5 text-sm font-semibold text-ink shadow-lg transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl"
        >
          Try it now
          <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
        </Link>
      </div>
    </section>
  );
}
