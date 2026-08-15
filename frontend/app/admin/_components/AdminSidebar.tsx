"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  AudioLines,
  CalendarDays,
  LayoutGrid,
  LogOut,
  Menu,
  ShieldAlert,
  Users,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { adminApi } from "@/lib/adminApi";

const links: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/admin", label: "Overview", icon: LayoutGrid },
  { href: "/admin/appointments", label: "Appointments", icon: CalendarDays },
  { href: "/admin/patients", label: "Patients", icon: Users },
  { href: "/admin/escalations", label: "Escalations", icon: ShieldAlert },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await adminApi.logout();
    } finally {
      router.push("/admin/login");
    }
  }

  const navContent = (
    <>
      <Link href="/admin" className="flex items-center gap-2 px-2 group">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-ink text-white transition-transform duration-300 group-hover:scale-105">
          <AudioLines className="h-4 w-4" strokeWidth={2.25} />
        </span>
        <span className="font-display text-[15px] font-extrabold tracking-tight text-ink">
          Recepta
        </span>
        <span className="rounded-full border border-line bg-paper px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted">
          Admin
        </span>
      </Link>

      <nav className="mt-8 flex flex-1 flex-col gap-1 px-2">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors duration-200 ${
                active
                  ? "bg-ink text-white"
                  : "text-muted hover:bg-ink/5 hover:text-ink"
              }`}
            >
              <link.icon className="h-4 w-4 shrink-0" strokeWidth={2} />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-2 pb-2">
        <button
          type="button"
          onClick={handleLogout}
          disabled={loggingOut}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted transition-colors duration-200 hover:bg-red-500/10 hover:text-red-500 disabled:opacity-50"
        >
          <LogOut className="h-4 w-4 shrink-0" strokeWidth={2} />
          {loggingOut ? "Signing out…" : "Log out"}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile top bar */}
      <div className="flex items-center justify-between border-b border-line bg-surface px-4 py-3 lg:hidden">
        <Link href="/admin" className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-ink text-white">
            <AudioLines className="h-3.5 w-3.5" strokeWidth={2.25} />
          </span>
          <span className="font-display text-sm font-extrabold tracking-tight text-ink">
            Recepta Admin
          </span>
        </Link>
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-ink transition-colors hover:bg-ink/5"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" strokeWidth={2} />
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-ink/40 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <div className="reveal absolute inset-y-0 left-0 flex w-72 max-w-[80vw] flex-col border-r border-line bg-surface py-5">
            <div className="mb-2 flex items-center justify-end px-2">
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-ink/5 hover:text-ink"
                aria-label="Close menu"
              >
                <X className="h-4 w-4" strokeWidth={2} />
              </button>
            </div>
            {navContent}
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-64 shrink-0 flex-col border-r border-line bg-surface py-6 lg:flex">
        {navContent}
      </aside>
    </>
  );
}
