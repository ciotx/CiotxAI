"use client";

import { getMe, logout } from "@/lib/api";
import { LogOut, Plus, Scan, Shield } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface User {
  id: string;
  email: string;
  name: string | null;
  plan: string;
  plan_status: string;
  trial_ends_at: string | null;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe().then((u) => {
      if (!u) {
        router.push("/login");
        return;
      }
      setUser(u);
      setLoading(false);
    });
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-text-secondary text-sm">Loading...</div>
      </div>
    );
  }

  if (!user) return null;

  const isTrial = user.plan_status === "trial";
  const isPro = user.plan === "pro";

  return (
    <div className="min-h-screen bg-bg-base">
      {/* Header */}
      <header className="border-b border-border-subtle">
        <div className="max-w-[1200px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-accent" />
            <span className="font-semibold tracking-tight text-text-primary">CIOTX</span>
          </div>

          <div className="flex items-center gap-4">
            {isTrial ? (
              <span className="text-xs bg-status-warning/10 text-status-warning px-2 py-1 rounded-full font-medium">
                Trial · 7 days left
              </span>
            ) : (
              <span className="text-xs bg-status-success/10 text-status-success px-2 py-1 rounded-full font-medium">
                {isPro ? "Pro" : "Starter"} · Active
              </span>
            )}

            <span className="text-sm text-text-secondary">{user.email}</span>

            <button
              onClick={logout}
              className="text-text-tertiary hover:text-text-secondary transition-colors"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1200px] mx-auto px-6 py-12">
        {/* Welcome */}
        <div className="mb-12">
          <h1 className="text-2xl font-semibold tracking-tight mb-2">
            Welcome{user.name ? `, ${user.name.split(" ")[0]}` : ""}
          </h1>
          <p className="text-text-secondary text-sm">
            {isTrial
              ? "Your 7-day Pro trial is active. Subscribe to keep scanning after the trial."
              : `${user.plan === "pro" ? "Pro" : "Starter"} plan — ready to scan.`}
          </p>
        </div>

        {/* Empty state */}
        <div className="bg-bg-surface border border-border-subtle rounded-xl p-12 flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-full bg-bg-hover flex items-center justify-center mb-6">
            <Scan className="w-8 h-8 text-text-tertiary" />
          </div>
          <h2 className="text-lg font-semibold mb-2">No projects yet</h2>
          <p className="text-text-secondary text-sm max-w-md mb-8">
            Connect a GitHub repository or scan a local project from the CLI to get started.
          </p>

          <div className="flex gap-3">
            <button
              onClick={() => {}}
              className="flex items-center gap-2 bg-accent text-accent-text font-medium text-sm px-4 py-2.5 rounded-md hover:bg-accent-hover active:scale-[0.98] transition-all"
            >
              <Plus className="w-4 h-4" />
              Connect Repository
            </button>
            <button
              onClick={() => {}}
              className="flex items-center gap-2 bg-bg-hover text-text-primary text-sm px-4 py-2.5 rounded-md border border-border-subtle hover:border-border-default transition-colors"
            >
              Scan from CLI
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
