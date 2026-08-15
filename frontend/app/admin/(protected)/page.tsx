"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  CalendarCheck,
  CalendarClock,
  CircleX,
  Percent,
  ShieldAlert,
  TriangleAlert,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  adminApi,
  formatDateTime,
  formatRelativeTime,
  type AdminStats,
  type Appointment,
  type Escalation,
} from "@/lib/adminApi";
import StatusPill from "@/app/admin/_components/StatusPill";
import EmptyState from "@/app/admin/_components/EmptyState";
import { SkeletonStatCard, SkeletonList } from "@/app/admin/_components/Skeletons";

type StatCardDef = {
  label: string;
  value: string;
  icon: LucideIcon;
  tone: "brand" | "alert" | "danger";
};

const toneClasses: Record<StatCardDef["tone"], string> = {
  brand: "bg-brand/10 text-brand",
  alert: "bg-alert/15 text-alert",
  danger: "bg-red-500/10 text-red-500",
};

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [appointments, setAppointments] = useState<Appointment[] | null>(null);
  const [escalations, setEscalations] = useState<Escalation[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.all([adminApi.stats(), adminApi.appointments(), adminApi.escalations()])
      .then(([statsRes, appointmentsRes, escalationsRes]) => {
        if (cancelled) return;
        setStats(statsRes);
        setAppointments(appointmentsRes);
        setEscalations(escalationsRes);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? "Failed to load dashboard data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const statCards: StatCardDef[] | null = stats
    ? [
        {
          label: "Total Bookings",
          value: stats.total_bookings.toLocaleString(),
          icon: CalendarCheck,
          tone: "brand",
        },
        {
          label: "Upcoming Appointments",
          value: stats.upcoming_appointments.toLocaleString(),
          icon: CalendarClock,
          tone: "brand",
        },
        {
          label: "Cancelled",
          value: stats.cancelled_appointments.toLocaleString(),
          icon: CircleX,
          tone: "danger",
        },
        {
          label: "Cancellation Rate",
          value: `${stats.cancellation_rate}%`,
          icon: Percent,
          tone: "alert",
        },
        {
          label: "Escalations This Week",
          value: stats.escalations_this_week.toLocaleString(),
          icon: ShieldAlert,
          tone: "danger",
        },
        {
          label: "Total Patients",
          value: stats.total_patients.toLocaleString(),
          icon: Users,
          tone: "brand",
        },
      ]
    : null;

  const recentEscalations = escalations?.slice(0, 5) ?? null;
  const recentAppointments = appointments?.slice(0, 5) ?? null;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
          Overview
        </h1>
        <p className="mt-1.5 text-sm text-muted">
          A snapshot of bookings, patients, and escalations.
        </p>
      </div>

      {error && (
        <div className="mb-6 flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-500">
          <TriangleAlert className="h-4 w-4 shrink-0" strokeWidth={2.25} />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {statCards
          ? statCards.map((card) => (
              <div
                key={card.label}
                className="rounded-2xl border border-line bg-surface p-6 transition-shadow duration-300 hover:shadow-lg hover:shadow-ink/5"
              >
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-lg ${toneClasses[card.tone]}`}
                >
                  <card.icon className="h-4 w-4" strokeWidth={2} />
                </div>
                <p className="mt-5 font-display text-3xl font-extrabold tracking-tight text-ink">
                  {card.value}
                </p>
                <p className="mt-1.5 text-sm font-medium text-muted">{card.label}</p>
              </div>
            ))
          : loading
            ? Array.from({ length: 6 }).map((_, i) => <SkeletonStatCard key={i} />)
            : null}
      </div>

      <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-lg font-bold tracking-tight text-ink">
              Recent Escalations
            </h2>
            <Link
              href="/admin/escalations"
              className="inline-flex items-center gap-1 text-sm font-semibold text-brand transition-colors hover:text-brand-dark"
            >
              View all
              <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={2.25} />
            </Link>
          </div>

          {loading ? (
            <SkeletonList count={3} />
          ) : (recentEscalations ?? []).length === 0 ? (
            <EmptyState
              icon={ShieldAlert}
              title="No escalations yet"
              description="Emergency and general escalations will show up here."
            />
          ) : (
            <div className="space-y-3">
              {(recentEscalations ?? []).map((esc) => (
                <div
                  key={esc.id}
                  className="rounded-2xl border border-line bg-surface p-5 transition-shadow duration-300 hover:shadow-lg hover:shadow-ink/5"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${
                        esc.reason === "emergency"
                          ? "bg-red-500/10 text-red-500"
                          : "bg-line/60 text-muted"
                      }`}
                    >
                      {esc.reason === "emergency" ? (
                        <TriangleAlert className="h-3 w-3" strokeWidth={2.5} />
                      ) : (
                        <ShieldAlert className="h-3 w-3" strokeWidth={2.5} />
                      )}
                      {esc.reason === "emergency" ? "Emergency" : "General"}
                    </span>
                    <span className="shrink-0 text-xs font-medium text-muted">
                      {formatRelativeTime(esc.timestamp)}
                    </span>
                  </div>
                  <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-ink">
                    {esc.message}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-lg font-bold tracking-tight text-ink">
              Recent Appointments
            </h2>
            <Link
              href="/admin/appointments"
              className="inline-flex items-center gap-1 text-sm font-semibold text-brand transition-colors hover:text-brand-dark"
            >
              View all
              <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={2.25} />
            </Link>
          </div>

          {loading ? (
            <SkeletonList count={3} />
          ) : (recentAppointments ?? []).length === 0 ? (
            <EmptyState
              icon={CalendarCheck}
              title="No appointments yet"
              description="Bookings made through the receptionist will appear here."
            />
          ) : (
            <div className="space-y-3">
              {(recentAppointments ?? []).map((appt) => (
                <div
                  key={appt.id}
                  className="rounded-2xl border border-line bg-surface p-5 transition-shadow duration-300 hover:shadow-lg hover:shadow-ink/5"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="truncate text-sm font-semibold text-ink">
                      {appt.patient_name}
                    </p>
                    <StatusPill status={appt.status} />
                  </div>
                  <p className="mt-1.5 truncate text-sm text-muted">{appt.reason}</p>
                  <p className="mt-2 text-xs font-medium text-muted">
                    {formatDateTime(appt.scheduled_time)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
