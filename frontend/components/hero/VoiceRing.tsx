"use client";

import { Phone } from "lucide-react";

const BAR_COUNT = 32;
const RADIUS = 108;

export default function VoiceRing() {
  const bars = Array.from({ length: BAR_COUNT }, (_, i) => {
    const angle = (360 / BAR_COUNT) * i;
    const delay = (i % 8) * 0.12;
    const duration = 1.3 + (i % 5) * 0.15;
    return { angle, delay, duration };
  });

  return (
    <div className="relative mx-auto h-[280px] w-[280px] sm:h-[320px] sm:w-[320px]">
      {/* ambient glow */}
      <div
        className="absolute inset-0 rounded-full opacity-60 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, var(--color-brand) 0%, transparent 70%)",
        }}
      />

      {/* radial bars */}
      <div className="absolute inset-0">
        {bars.map((bar, i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 h-6 w-[3px] origin-bottom rounded-full bg-brand/70"
            style={{
              transform: `rotate(${bar.angle}deg) translateY(-${RADIUS}px)`,
            }}
          >
            <span
              className="animate-bar block h-full w-full origin-bottom rounded-full bg-brand"
              style={{
                animationDelay: `${bar.delay}s`,
                animationDuration: `${bar.duration}s`,
              }}
            />
          </div>
        ))}
      </div>

      {/* center orb */}
      <div className="absolute left-1/2 top-1/2 flex h-24 w-24 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-ink shadow-[0_20px_50px_-12px_rgba(18,20,43,0.5)]">
        <div className="absolute inset-0 rounded-full bg-white/10" />
        <Phone className="h-8 w-8 text-white" strokeWidth={1.75} />
      </div>

      {/* floating transcript chips */}
      <div
        className="animate-drift absolute -left-4 top-6 rounded-2xl border border-line bg-surface px-3 py-2 text-xs font-medium text-ink shadow-lg shadow-ink/5 sm:-left-10"
        style={{ animationDelay: "0.3s" }}
      >
        &quot;Book me Tuesday at 2 PM&quot;
      </div>
      <div
        className="animate-drift absolute -right-2 bottom-10 rounded-2xl border border-line bg-surface px-3 py-2 text-xs font-medium text-live shadow-lg shadow-ink/5 sm:-right-8"
        style={{ animationDelay: "1.6s" }}
      >
        Confirmed for Tue, 2:00 PM
      </div>
    </div>
  );
}
