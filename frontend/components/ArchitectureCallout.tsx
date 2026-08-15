import { Network, Building2, Clock, Link2 } from "lucide-react";

const points = [
  {
    icon: Building2,
    title: "Isolated knowledge base per tenant",
    detail: "Each clinic gets its own vector namespace — no cross-contamination of FAQs.",
  },
  {
    icon: Clock,
    title: "Configurable hours & policies",
    detail: "Booking rules, holidays, and escalation logic are per-tenant config, not code.",
  },
  {
    icon: Link2,
    title: "Tool access via MCP servers",
    detail: "Calendar and email integrations are pluggable MCP tool servers, swappable per business.",
  },
];

export default function ArchitectureCallout() {
  return (
    <section className="px-6 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl">
        <div className="grid grid-cols-1 gap-14 lg:grid-cols-2 lg:items-center">
          <div className="reveal">
            <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-brand">
              <Network className="h-4 w-4" />
              Built to scale
            </p>
            <h2 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
              One receptionist engine,
              <br />
              many clinics.
            </h2>
            <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-muted">
              The LangGraph pipeline underneath this demo is designed as
              multi-tenant infrastructure from day one — this instance just
              runs a single clinic to keep the demo simple.
            </p>

            <ul className="mt-8 space-y-5">
              {points.map((point) => (
                <li key={point.title} className="flex gap-4">
                  <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
                    <point.icon className="h-4 w-4" strokeWidth={1.9} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ink">{point.title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-muted">
                      {point.detail}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="reveal" style={{ animationDelay: "0.1s" }}>
            <div className="overflow-hidden rounded-2xl bg-ink shadow-2xl shadow-ink/20">
              <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-3">
                <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
                <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
                <span className="ml-2 font-mono text-xs text-white/40">
                  tenant.config.ts
                </span>
              </div>
              <div className="overflow-x-auto px-5 py-6 font-mono text-[13px] leading-relaxed">
                <div className="text-white/40">{"// registered per clinic"}</div>
                <div className="whitespace-pre text-white/70">
                  export const <span className="text-sky-300">tenant</span> = {"{"}
                </div>
                <div className="whitespace-pre text-white/70">
                  {"  id: "}
                  <span className="text-emerald-300">&quot;brightpath-clinic&quot;</span>,
                </div>
                <div className="whitespace-pre text-white/70">
                  {"  vectorNamespace: "}
                  <span className="text-emerald-300">&quot;brightpath::faq-v2&quot;</span>,
                </div>
                <div className="whitespace-pre text-white/70">
                  {"  hours: { "}
                  <span className="text-sky-300">mon_fri</span>
                  {": "}
                  <span className="text-emerald-300">&quot;8:00–18:00&quot;</span>
                  {", "}
                  <span className="text-sky-300">sat</span>
                  {": "}
                  <span className="text-emerald-300">&quot;9:00–13:00&quot;</span>
                  {" },"}
                </div>
                <div className="whitespace-pre text-white/70">
                  {"  calendar: "}
                  <span className="text-amber-300">mcp</span>
                  {"("}
                  <span className="text-emerald-300">&quot;google-calendar&quot;</span>
                  {"),"}
                </div>
                <div className="whitespace-pre text-white/70">
                  {"  notifications: "}
                  <span className="text-amber-300">mcp</span>
                  {"("}
                  <span className="text-emerald-300">&quot;email&quot;</span>
                  {"),"}
                </div>
                <div className="text-white/70">{"}"}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
