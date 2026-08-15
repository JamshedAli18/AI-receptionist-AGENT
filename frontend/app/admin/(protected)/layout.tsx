"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AudioLines } from "lucide-react";
import { adminApi } from "@/lib/adminApi";
import AdminSidebar from "@/app/admin/_components/AdminSidebar";
import Spinner from "@/app/admin/_components/Spinner";

export default function ProtectedAdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [status, setStatus] = useState<"checking" | "authed">("checking");

  useEffect(() => {
    let cancelled = false;

    adminApi
      .check()
      .then((res) => {
        if (cancelled) return;
        if (res.authenticated) {
          setStatus("authed");
        } else {
          router.replace("/admin/login");
        }
      })
      .catch(() => {
        if (!cancelled) router.replace("/admin/login");
      });

    return () => {
      cancelled = true;
    };
  }, [router]);

  if (status === "checking") {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-ink text-white">
          <AudioLines className="h-5 w-5" strokeWidth={2.25} />
        </span>
        <div className="flex items-center gap-2 text-sm font-medium text-muted">
          <Spinner className="h-4 w-4" />
          Checking session…
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col lg:flex-row">
      <AdminSidebar />
      <main className="flex-1 px-5 py-8 sm:px-8 lg:px-10">{children}</main>
    </div>
  );
}
