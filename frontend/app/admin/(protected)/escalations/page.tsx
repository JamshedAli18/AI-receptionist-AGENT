"use client";

import { useEffect, useMemo, useState } from "react";
import { ShieldAlert, TriangleAlert } from "lucide-react";
import { adminApi, formatRelativeTime, type Escalation, type EscalationReason } from "@/lib/adminApi";
import EmptyState from "@/app/admin/_components/EmptyState";
import { SkeletonList } from "@/app/admin/_components/Skeletons";

type FilterValue = "all" | EscalationReason;

const filters: { value: FilterValue; label: string }[] = [
  { value: "all", label: "All" },
  { value: "emergency", label: "Emergency only" },
  { value: "general", label: "General only" },
];

export default function AdminEscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterValue>("all");

  useEffect(() => {
    let cancelled = false;

    adminApi
      .escalations()
      .then((res) => {
        if (!cancelled) setEscalations(res);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? "Failed to load escalations.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const source = escalations ?? [];
    if (filter === "all") return source;
    return source.filter((e) => e.reason === filter);
  }, [escalations, filter]);

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
            Escalations
          </h1>
          <p className="mt-1.5 text-sm text-muted">
            Calls flagged as emergencies or routed to a human.
          </p>
        </div>

        <div className="no-scrollbar inline-flex max-w-full items-center gap-1 overflow-x-auto rounded-full border border-line bg-surface p-1 shadow-sm">
          {filters.map((f) => {
            const active = filter === f.value;
            return (
              <button
                key={f.value}
                type="button"
                onClick={() => setFilter(f.value)}
                className={`shrink-0 whitespace-nowrap rounded-full px-3.5 py-2 text-[13px] font-medium transition-all duration-200 sm:text-sm ${
                  active ? "bg-ink text-white shadow-sm" : "text-muted hover:text-ink"
                }`}
              >
                {f.label}
              </button>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="mb-6 flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-500">
          <TriangleAlert className="h-4 w-4 shrink-0" strokeWidth={2.25} />
          {error}
        </div>
      )}

      {loading ? (
        <SkeletonList count={5} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={ShieldAlert}
          title="Nothing here yet"
          description={
            filter === "all"
              ? "Emergency and general escalations will show up here."
              : `No ${filter} escalations to show.`
          }
        />
      ) : (
        <div className="space-y-4">
          {filtered.map((esc) => {
            const isEmergency = esc.reason === "emergency";
            return (
              <div
                key={esc.id}
                className={`rounded-2xl border bg-surface p-5 transition-shadow duration-300 hover:shadow-lg hover:shadow-ink/5 ${
                  isEmergency ? "border-red-500/25" : "border-line"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${
                        isEmergency ? "bg-red-500/10 text-red-500" : "bg-line/60 text-muted"
                      }`}
                    >
                      {isEmergency ? (
                        <TriangleAlert className="h-3 w-3" strokeWidth={2.5} />
                      ) : (
                        <ShieldAlert className="h-3 w-3" strokeWidth={2.5} />
                      )}
                      {isEmergency ? "Emergency" : "General"}
                    </span>
                    {esc.category && (
                      <span className="rounded-full border border-line bg-paper px-2.5 py-1 text-xs font-medium text-muted">
                        {esc.category}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-medium text-muted">
                    {formatRelativeTime(esc.timestamp)}
                  </span>
                </div>

                <blockquote className="mt-3.5 border-l-2 border-line pl-3.5 text-sm leading-relaxed text-ink">
                  {esc.message}
                </blockquote>

                <p className="mt-3 font-mono text-[11px] text-muted/80">{esc.call_sid}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
