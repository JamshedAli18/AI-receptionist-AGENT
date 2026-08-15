import { MessagesSquare, BookOpenCheck, ShieldAlert, CalendarSync, LayoutDashboard } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type Feature = {
  icon: LucideIcon;
  title: string;
  description: string;
};

const features: Feature[] = [
  {
    icon: MessagesSquare,
    title: "Natural conversation booking",
    description:
      "Patients speak the way they would to a human — Recepta books, reschedules, or cancels appointments in the same call.",
  },
  {
    icon: BookOpenCheck,
    title: "Instant, grounded FAQ answers",
    description:
      "Retrieval-augmented answers pulled from your clinic's real hours, policies, and services — never made up.",
  },
  {
    icon: ShieldAlert,
    title: "Emergency detection & escalation",
    description:
      "Recognizes urgent symptoms mid-conversation and safely routes the caller to emergency guidance instead of a booking flow.",
  },
  {
    icon: CalendarSync,
    title: "Calendar & email sync",
    description:
      "Every booking lands directly on the clinic's Google Calendar with automatic confirmation and reminder emails.",
  },
  {
    icon: LayoutDashboard,
    title: "Staff Dashboard",
    description:
      "Real-time visibility into bookings, patients, and escalations for clinic staff.",
  },
];

export default function FeatureGrid() {
  return (
    <section className="px-6 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="reveal max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand">
            What it handles
          </p>
          <h2 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
            Everything the front desk does, minus the wait.
          </h2>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature, i) => (
            <div
              key={feature.title}
              className="reveal group rounded-2xl border border-line bg-surface p-6 transition-all duration-300 hover:-translate-y-1 hover:border-brand/30 hover:shadow-xl hover:shadow-ink/5"
              style={{ animationDelay: `${i * 0.08}s` }}
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand/10 text-brand transition-colors duration-300 group-hover:bg-brand group-hover:text-white">
                <feature.icon className="h-5 w-5" strokeWidth={1.9} />
              </div>
              <h3 className="mt-5 text-[15px] font-semibold text-ink">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
