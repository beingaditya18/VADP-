"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { CaseCard } from "@/components/cases/case-card";
import { useCases } from "@/hooks/use-cases";
import { useAuth } from "@/hooks/use-auth";
import { Scale, Sparkles, Clock, ShieldCheck, LogOut, Loader2 } from "lucide-react";

export default function JudgePortalPage() {
  const { user, logout } = useAuth();
  const { cases, totalCases, isLoading, fetchCases } = useCases();

  useEffect(() => {
    fetchCases({ page: 1 });
  }, [fetchCases]);

  return (
    <AuthGuard allowedRoles={["judge", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Header */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Scale className="h-5 w-5" />
              </div>
              <span className="font-bold tracking-tight text-lg text-white">Judge Master Bench Portal</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400">
                Hon'ble <strong className="text-white">{user?.full_name}</strong>
              </span>
              <button
                onClick={logout}
                className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" /> Sign Out
              </button>
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="mx-auto max-w-7xl px-6 py-10 space-y-8">
          <div className="glass rounded-2xl p-8 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">
                Welcome, Hon'ble Judge {user?.full_name}
              </h1>
              <p className="text-sm text-gray-400">
                Review assigned case dockets, evaluate SHAP explainability metrics, and perform decision reviews.
              </p>
            </div>
          </div>

          {/* Cases List */}
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-400" /> Assigned Case Bench Docket
            </h2>

            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
              </div>
            ) : cases.length === 0 ? (
              <div className="glass rounded-2xl p-12 text-center text-gray-400 border border-white/5">
                No cases pending on judicial bench docket.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {cases.map((c) => (
                  <CaseCard key={c.id} caseObj={c} hrefPrefix="/judge/cases" />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
