"use client";

import { useEffect, useState } from "react";
import { Users, TriangleAlert } from "lucide-react";
import { adminApi, formatDate, type Patient } from "@/lib/adminApi";
import EmptyState from "@/app/admin/_components/EmptyState";
import { SkeletonRow, SkeletonList } from "@/app/admin/_components/Skeletons";

export default function AdminPatientsPage() {
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    adminApi
      .patients()
      .then((res) => {
        if (!cancelled) setPatients(res);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message ?? "Failed to load patients.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
          Patients
        </h1>
        <p className="mt-1.5 text-sm text-muted">Everyone who has called in.</p>
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
      ) : (patients ?? []).length === 0 ? (
        <EmptyState
          icon={Users}
          title="Nothing here yet"
          description="Patients who call in will show up here once they book."
        />
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden overflow-x-auto rounded-2xl border border-line bg-surface md:block">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/60 text-xs font-semibold uppercase tracking-wide text-muted">
                  <th className="px-5 py-3.5 font-semibold">Name</th>
                  <th className="px-5 py-3.5 font-semibold">Email</th>
                  <th className="px-5 py-3.5 font-semibold">Age</th>
                  <th className="px-5 py-3.5 font-semibold">Total Bookings</th>
                  <th className="px-5 py-3.5 font-semibold">First Seen</th>
                  <th className="px-5 py-3.5 font-semibold">Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {(patients ?? []).map((patient) => (
                  <tr
                    key={patient.id}
                    className="border-b border-line text-ink last:border-0 hover:bg-paper/40"
                  >
                    <td className="px-5 py-4 font-medium">{patient.name}</td>
                    <td className="px-5 py-4 text-muted">{patient.email}</td>
                    <td className="px-5 py-4 text-muted">{patient.age}</td>
                    <td className="px-5 py-4 text-muted">{patient.total_bookings}</td>
                    <td className="px-5 py-4 whitespace-nowrap text-muted">
                      {formatDate(patient.first_seen)}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-muted">
                      {formatDate(patient.last_seen)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="space-y-3 md:hidden">
            {(patients ?? []).map((patient) => (
              <div key={patient.id} className="rounded-2xl border border-line bg-surface p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-ink">{patient.name}</p>
                    <p className="mt-0.5 truncate text-[13px] text-muted">{patient.email}</p>
                  </div>
                  <span className="shrink-0 rounded-full border border-line bg-paper px-2.5 py-1 text-xs font-semibold text-muted">
                    Age {patient.age}
                  </span>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs font-medium text-muted">
                  <span>{patient.total_bookings} bookings</span>
                  <span>
                    Last seen {formatDate(patient.last_seen)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
