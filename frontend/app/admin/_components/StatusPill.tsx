import type { AppointmentStatus } from "@/lib/adminApi";

const styles: Record<AppointmentStatus, string> = {
  booked: "bg-live/10 text-live",
  rescheduled: "bg-brand/10 text-brand",
  cancelled: "bg-red-500/10 text-red-500",
};

const labels: Record<AppointmentStatus, string> = {
  booked: "Booked",
  rescheduled: "Rescheduled",
  cancelled: "Cancelled",
};

export default function StatusPill({ status }: { status: AppointmentStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${styles[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {labels[status]}
    </span>
  );
}
