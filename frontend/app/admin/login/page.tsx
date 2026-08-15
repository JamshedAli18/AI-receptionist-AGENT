"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AudioLines, Eye, EyeOff, Lock, TriangleAlert } from "lucide-react";
import { adminApi, AdminApiError } from "@/lib/adminApi";
import Spinner from "@/app/admin/_components/Spinner";

export default function AdminLoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!password || submitting) return;

    setSubmitting(true);
    setError(null);
    try {
      await adminApi.login(password);
      router.push("/admin");
    } catch (err) {
      if (err instanceof AdminApiError && err.status === 401) {
        setError("Incorrect password. Please try again.");
      } else if (err instanceof AdminApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
      setSubmitting(false);
    }
  }

  return (
    <div className="relative flex min-h-[calc(100vh-4rem)] items-center justify-center overflow-hidden px-6 py-16">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[420px] opacity-[0.15] blur-3xl"
        style={{
          background:
            "radial-gradient(55% 55% at 50% 0%, var(--color-brand) 0%, transparent 70%)",
        }}
      />

      <div className="reveal w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-ink text-white">
            <AudioLines className="h-5 w-5" strokeWidth={2.25} />
          </span>
          <h1 className="mt-5 font-display text-2xl font-extrabold tracking-tight text-ink">
            Admin Access
          </h1>
          <p className="mt-2 text-sm text-muted">
            Sign in with the admin password to manage Recepta.
          </p>
        </div>

        <div className="rounded-[28px] border border-line bg-surface p-7 shadow-xl shadow-ink/5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted"
              >
                Password
              </label>
              <div className="relative">
                <Lock
                  className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                  strokeWidth={2}
                />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoFocus
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="Enter admin password"
                  className="w-full rounded-xl border border-line bg-paper py-3 pl-10 pr-11 text-sm text-ink outline-none transition-colors placeholder:text-muted/60 focus:border-brand focus:ring-2 focus:ring-brand/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted transition-colors hover:text-ink"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" strokeWidth={2} />
                  ) : (
                    <Eye className="h-4 w-4" strokeWidth={2} />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-xl bg-red-50 px-3.5 py-2.5 text-[13px] font-medium text-red-500">
                <TriangleAlert className="h-4 w-4 shrink-0" strokeWidth={2.25} />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={!password || submitting}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-ink px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-ink/15 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-ink/20 disabled:pointer-events-none disabled:opacity-50 disabled:hover:translate-y-0"
            >
              {submitting ? (
                <>
                  <Spinner className="h-4 w-4 text-white/80" />
                  Signing in…
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
