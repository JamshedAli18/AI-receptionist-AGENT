import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import BusinessSwitcher from "@/components/BusinessSwitcher";
import VoiceWidget from "@/components/VoiceWidget";

export const metadata = {
  title: "Live Demo — Recepta",
};

export default function DemoPage() {
  return (
    <div className="relative flex min-h-[calc(100vh-4rem)] flex-col overflow-hidden px-4">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[420px] opacity-[0.12] blur-3xl"
        style={{
          background:
            "radial-gradient(55% 55% at 50% 0%, var(--color-brand) 0%, transparent 70%)",
        }}
      />

      <div className="mx-auto w-full max-w-xl pt-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-ink"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>
      </div>

      <div className="mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center gap-7 py-10">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand">
            Live demo
          </p>
          <h1 className="mt-2 font-display text-3xl font-extrabold tracking-tight text-ink">
            Talk to the receptionist
          </h1>
        </div>

        <BusinessSwitcher />

        <VoiceWidget />
      </div>
    </div>
  );
}
