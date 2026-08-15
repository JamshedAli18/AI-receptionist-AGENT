export function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-line/70 ${className}`} />;
}

export function SkeletonStatCard() {
  return (
    <div className="rounded-2xl border border-line bg-surface p-6">
      <SkeletonBlock className="h-9 w-9 rounded-lg" />
      <SkeletonBlock className="mt-5 h-7 w-16" />
      <SkeletonBlock className="mt-3 h-3.5 w-24" />
    </div>
  );
}

export function SkeletonRow({ cols = 4 }: { cols?: number }) {
  return (
    <tr className="border-b border-line last:border-0">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-5 py-4">
          <SkeletonBlock className="h-4 w-full max-w-32" />
        </td>
      ))}
    </tr>
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <div className="flex items-center justify-between">
        <SkeletonBlock className="h-4 w-32" />
        <SkeletonBlock className="h-5 w-16 rounded-full" />
      </div>
      <SkeletonBlock className="mt-3 h-3.5 w-48" />
      <SkeletonBlock className="mt-2 h-3.5 w-36" />
    </div>
  );
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
