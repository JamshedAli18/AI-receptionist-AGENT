"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, TriangleAlert } from "lucide-react";
import {
  adminApi,
  formatDateTime,
  formatRelativeTime,
  type Appointment,
  type AppointmentStatus,
} from "@/lib/adminApi";
import StatusPill from "@/app/admin/_components/StatusPill";
import EmptyState from "@/app/admin/_components/EmptyState";
import { SkeletonRow, SkeletonList } from "@/app/admin/_components/Skeletons";

type FilterValue = "all" | AppointmentStatus;

const filters: { value: FilterValue; label: string }[] = [
  { value: "all", label: "All" },
  { value: "booked", label: "Booked" },
  { value: "rescheduled", label: "Rescheduled" },
  { value: "cancelled", label: "Cancelled" },
];

export default function AdminAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterValue>("all");

  useEffect(() => {
    let cancelled = false;

    adminApi
      .appointments()
      .then((res) => {
        if (!cancelled) setAppointments(res);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? "Failed to load appointments.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    const source = appointments ?? [];
    if (filter === "all") return source;
    return source.filter((a) => a.status === filter);
  }, [appointments, filter]);

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
            Appointments
          </h1>
          <p className="mt-1.5 text-sm text-muted">
            Every booking made through the receptionist.
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
        <>
          <div className="hidden overflow-hidden rounded-2xl border border-line bg-surface md:block">
            <table className="w-full text-left text-sm">
              <tbody>
                {Array.from({ length: 6 }).map((_, i) => (
                  <SkeletonRow key={i} cols={6} />
                ))}
              </tbody>
            </table>
          </div>
          <div className="md:hidden">
            <SkeletonList count={4} />
          </div>
        </>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="Nothing here yet"
          description={
            filter === "all"
              ? "Bookings made through the receptionist will appear here."
              : `No ${filter} appointments to show.`
          }
        />
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden overflow-x-auto rounded-2xl border border-line bg-surface md:block">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/60 text-xs font-semibold uppercase tracking-wide text-muted">
                  <th className="px-5 py-3.5 font-semibold">Booking ID</th>
                  <th className="px-5 py-3.5 font-semibold">Patient</th>
                  <th className="px-5 py-3.5 font-semibold">Reason</th>
                  <th className="px-5 py-3.5 font-semibold">Scheduled Time</th>
                  <th className="px-5 py-3.5 font-semibold">Status</th>
                  <th className="px-5 py-3.5 font-semibold">Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((appt) => (
                  <tr
                    key={appt.id}
                    className="border-b border-line text-ink last:border-0 hover:bg-paper/40"
                  >
                    <td className="px-5 py-4 font-mono text-[13px] text-muted">
                      {appt.booking_id}
                    </td>
                    <td className="px-5 py-4 font-medium">{appt.patient_name}</td>
                    <td className="max-w-56 truncate px-5 py-4 text-muted">{appt.reason}</td>
                    <td className="px-5 py-4 whitespace-nowrap text-muted">
                      {formatDateTime(appt.scheduled_time)}
                    </td>
                    <td className="px-5 py-4">
                      <StatusPill status={appt.status} />
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-muted">
                      {formatRelativeTime(appt.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="space-y-3 md:hidden">
            {filtered.map((appt) => (
              <div
                key={appt.id}
                className="rounded-2xl border border-line bg-surface p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-ink">
                      {appt.patient_name}
                    </p>
                    <p className="mt-0.5 font-mono text-[12px] text-muted">
                      {appt.booking_id}
                    </p>
                  </div>
                  <StatusPill status={appt.status} />
                </div>
                <p className="mt-3 text-sm text-muted">{appt.reason}</p>
                <div className="mt-3 flex items-center justify-between text-xs font-medium text-muted">
                  <span>{formatDateTime(appt.scheduled_time)}</span>
                  <span>Created {formatRelativeTime(appt.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
