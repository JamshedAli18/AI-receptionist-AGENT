import Link from "next/link";
import { AudioLines, GitFork } from "lucide-react";

const badges = ["LangGraph", "Groq", "Deepgram", "MongoDB", "Next.js"];

export default function Footer() {
  return (
    <footer className="border-t border-line px-6 py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 sm:flex-row sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-ink text-white">
            <AudioLines className="h-3.5 w-3.5" strokeWidth={2.25} />
          </span>
          <span className="font-display text-sm font-extrabold tracking-tight text-ink">
            Recepta
          </span>
          <span className="text-sm text-muted">— AI receptionist demo</span>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2">
          {badges.map((badge) => (
            <span
              key={badge}
              className="rounded-full border border-line bg-surface px-3 py-1 font-mono text-[11px] font-medium text-muted"
            >
              {badge}
            </span>
          ))}
        </div>

        <div className="flex items-center gap-4">
          <Link
            href="/admin/login"
            className="text-xs font-medium text-muted/50 transition-colors hover:text-muted"
          >
            Staff Login
          </Link>
          <a
            href="https://github.com/JamshedAli18/AI-receptionist-AGENT"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-ink"
          >
            <GitFork className="h-4 w-4" />
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
