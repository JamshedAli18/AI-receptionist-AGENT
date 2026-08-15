import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

type EmptyStateProps = {
  icon?: LucideIcon;
  title?: string;
  description?: string;
};

export default function EmptyState({
  icon: Icon = Inbox,
  title = "Nothing here yet",
  description,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line bg-surface/60 px-6 py-16 text-center">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-paper text-muted">
        <Icon className="h-5 w-5" strokeWidth={1.75} />
      </div>
      <p className="text-sm font-semibold text-ink">{title}</p>
      {description && (
        <p className="max-w-xs text-sm leading-relaxed text-muted">{description}</p>
      )}
    </div>
  );
}
