"use client";

import { useState } from "react";
import { Stethoscope, Sparkles } from "lucide-react";

const businesses = [
  { id: "brightpath", name: "BrightPath Clinic", icon: Stethoscope, available: true },
  { id: "smile-dental", name: "Smile Dental", icon: Sparkles, available: false },
];

export default function BusinessSwitcher() {
  const [active, setActive] = useState("brightpath");

  return (
    <div className="no-scrollbar inline-flex max-w-full items-center gap-1 overflow-x-auto rounded-full border border-line bg-surface p-1 shadow-sm">
      {businesses.map((business) => {
        const isActive = active === business.id;
        return (
          <button
            key={business.id}
            type="button"
            disabled={!business.available}
            onClick={() => business.available && setActive(business.id)}
            title={business.available ? undefined : "Coming soon"}
            className={`relative flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-2 text-[13px] font-medium transition-all duration-200 sm:px-4 sm:text-sm ${
              isActive
                ? "bg-ink text-white shadow-sm"
                : business.available
                  ? "text-muted hover:text-ink"
                  : "cursor-not-allowed text-muted/50"
            }`}
          >
            <business.icon className="h-3.5 w-3.5 shrink-0" strokeWidth={2} />
            {business.name}
            {!business.available && (
              <span className="ml-1 rounded-full bg-paper px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted">
                Soon
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
