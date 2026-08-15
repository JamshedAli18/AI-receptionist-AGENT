const BASE = process.env.NEXT_PUBLIC_API_URL;

export class AdminApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
  }
}

async function adminFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  } catch {
    throw new AdminApiError(0, "Could not reach the server. Is the backend running?");
  }

  if (!res.ok) {
    let message = res.statusText || "Request failed";
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") message = body.detail;
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new AdminApiError(res.status, message);
  }

  return (await res.json()) as T;
}

export type AdminStats = {
  total_bookings: number;
  upcoming_appointments: number;
  cancelled_appointments: number;
  cancellation_rate: number;
  escalations_this_week: number;
  total_patients: number;
};

export type AppointmentStatus = "booked" | "rescheduled" | "cancelled";

export type AppointmentHistoryEntry = {
  action: string;
  time: string;
  [key: string]: unknown;
};

export type Appointment = {
  id: string;
  booking_id: string;
  patient_name: string;
  patient_age: number;
  patient_email: string;
  reason: string;
  status: AppointmentStatus;
  scheduled_time: string;
  created_at: string;
  updated_at: string;
  history: AppointmentHistoryEntry[];
};

export type Patient = {
  id: string;
  name: string;
  email: string;
  age: number;
  first_seen: string;
  last_seen: string;
  total_bookings: number;
};

export type EscalationReason = "emergency" | "general";

export type Escalation = {
  id: string;
  call_sid: string;
  reason: EscalationReason;
  category: string | null;
  message: string;
  timestamp: string;
};

export const adminApi = {
  login: (password: string) =>
    adminFetch<{ status: string }>("/admin/api/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),
  logout: () => adminFetch<{ status: string }>("/admin/api/logout", { method: "POST" }),
  check: () => adminFetch<{ authenticated: boolean }>("/admin/api/check"),
  stats: () => adminFetch<AdminStats>("/admin/api/stats"),
  appointments: () => adminFetch<Appointment[]>("/admin/api/appointments"),
  patients: () => adminFetch<Patient[]>("/admin/api/patients"),
  escalations: () => adminFetch<Escalation[]>("/admin/api/escalations"),
};

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  const datePart = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const timePart = date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${datePart} · ${timePart}`;
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";

  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.round(diffMs / 1000);
  const diffMin = Math.round(diffSec / 60);
  const diffHour = Math.round(diffMin / 60);
  const diffDay = Math.round(diffHour / 24);

  if (Math.abs(diffSec) < 45) return "just now";
  if (Math.abs(diffMin) < 60) return rtf(diffMin, "minute");
  if (Math.abs(diffHour) < 24) return rtf(diffHour, "hour");
  if (Math.abs(diffDay) < 30) return rtf(diffDay, "day");

  return formatDate(iso);
}

function rtf(value: number, unit: "minute" | "hour" | "day"): string {
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  return formatter.format(-value, unit);
}
