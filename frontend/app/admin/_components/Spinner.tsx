import { LoaderCircle } from "lucide-react";

export default function Spinner({ className = "h-5 w-5" }: { className?: string }) {
  return <LoaderCircle className={`animate-spin text-muted ${className}`} strokeWidth={2} />;
}
