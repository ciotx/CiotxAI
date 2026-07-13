"use client";

import { api, verifyEmail } from "@/lib/api";
import { Shield, Check } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

function VerifyForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const userCode = searchParams.get("code") || "";
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // PKCE CLI auth mode (when ?code= is present)
  if (userCode) {
    async function authorizeCLI() {
      setLoading(true);
      setError("");
      const res = await api(`/v1/auth/cli/verify?user_code=${userCode}`, { method: "POST" });
      if (res.ok) {
        setLoading(false);
        // Show success state — user can close this tab
      } else {
        const err = await res.json().catch(() => ({ detail: "Authorization failed." }));
        setError(err.detail || "Authorization failed. Are you logged in?");
        setLoading(false);
      }
    }

    if (loading === false && error === "" && code === "done") {
      return (
        <div className="min-h-screen flex items-center justify-center px-4">
          <div className="w-full max-w-sm text-center">
            <div className="w-16 h-16 rounded-full bg-status-success/10 flex items-center justify-center mx-auto mb-6">
              <Check className="w-8 h-8 text-status-success" />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight mb-2">Authorized</h1>
            <p className="text-text-secondary text-sm">You can close this tab and return to the CLI.</p>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="w-16 h-16 rounded-full bg-bg-hover flex items-center justify-center mx-auto mb-6">
            <Shield className="w-8 h-8 text-accent" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight mb-2">CIOTX CLI Authorization</h1>
          <p className="text-text-secondary text-sm mb-8">
            A CIOTX CLI instance is requesting authorization. Code: <span className="font-mono text-text-primary">{userCode}</span>
          </p>

          {error && (
            <div className="bg-severity-critical/10 border border-severity-critical/30 text-severity-critical text-sm px-4 py-3 rounded-md mb-4">
              {error}
            </div>
          )}

          <button
            onClick={() => { authorizeCLI(); setCode("done"); }}
            disabled={loading}
            className="w-full bg-accent text-accent-text font-medium text-sm py-2.5 rounded-md hover:bg-accent-hover active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {loading ? "Authorizing..." : "Authorize CLI"}
          </button>
        </div>
      </div>
    );
  }

  // Email verification mode (when ?email= is present)
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await verifyEmail(email, code);
    setLoading(false);

    if (result.success) {
      router.push("/login?verified=true");
    } else {
      setError(result.error || "Verification failed.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-3 mb-8">
          <Shield className="w-8 h-8 text-accent" />
          <span className="text-xl font-semibold tracking-tight text-text-primary">CIOTX</span>
        </div>

        <h1 className="text-2xl font-semibold tracking-tight text-center mb-2">
          Verify your email
        </h1>
        <p className="text-sm text-text-secondary text-center mb-8">
          We sent a 6-digit code to{" "}
          <span className="text-text-primary">{email || "your email"}</span>
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-severity-critical/10 border border-severity-critical/30 text-severity-critical text-sm px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="code" className="block text-sm text-text-secondary mb-2">
              Verification code
            </label>
            <input
              id="code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              required
              maxLength={6}
              className="w-full bg-bg-surface border border-border-subtle rounded-md px-4 py-2.5 text-sm text-text-primary text-center tracking-[0.5em] font-mono placeholder:text-text-tertiary focus:outline-none focus:border-border-default transition-colors"
              placeholder="000000"
            />
          </div>

          <button
            type="submit"
            disabled={loading || code.length !== 6}
            className="w-full bg-accent text-accent-text font-medium text-sm py-2.5 rounded-md hover:bg-accent-hover active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Verifying..." : "Verify email"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-text-secondary">Loading...</div>}>
      <VerifyForm />
    </Suspense>
  );
}
