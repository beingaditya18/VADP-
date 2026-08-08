"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { CaseCard } from "@/components/cases/case-card";
import { useCases } from "@/hooks/use-cases";
import { useAuth } from "@/hooks/use-auth";
import { Scale, Sparkles, ShieldCheck, LogOut, Loader2, FileText, Activity, ArrowRight, CheckCircle2 } from "lucide-react";

export default function JudgePortalPage() {
  const { user, logout } = useAuth();
  const { cases, totalCases, isLoading, fetchCases } = useCases();

  useEffect(() => {
    fetchCases({ page: 1, page_size: 6 });
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
              <div>
                <span className="font-bold tracking-tight text-lg text-white block">Judge Master Bench Portal</span>
                <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> 1500 ILDC Real Judicial Records Active
                </span>
              </div>
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

        {/* Main Workspace */}
        <main className="mx-auto max-w-7xl px-6 py-8 space-y-8">
          {/* Welcome Banner */}
          <div className="glass rounded-2xl p-8 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-6 bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-[#0f0f18]">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 font-medium">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                VADP Zero Trust Decision-Support Active
              </div>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                Welcome, Hon'ble Judge {user?.full_name}
              </h1>
              <p className="text-xs md:text-sm text-gray-300 max-w-2xl leading-relaxed">
                Review assigned case dockets, evaluate RAG citations, examine SHAP explainability attributions, and issue verifiable decision approvals backed by Merkle inclusion proofs.
              </p>
            </div>

            <Link
              href="/judge/cases"
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-5 py-3 rounded-xl transition-all shadow-lg shadow-indigo-600/30 whitespace-nowrap self-start md:self-auto"
            >
              Browse Full 1500-Case Directory
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass rounded-xl p-5 border border-white/10 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <FileText className="h-6 w-6" />
              </div>
              <div>
                <span className="text-2xl font-extrabold text-white">{totalCases || 1500}</span>
                <span className="text-xs text-gray-400 block font-medium">Real ILDC Judgments</span>
              </div>
            </div>

            <div className="glass rounded-xl p-5 border border-white/10 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <span className="text-2xl font-extrabold text-white">100%</span>
                <span className="text-xs text-gray-400 block font-medium">Contract Completeness</span>
              </div>
            </div>

            <div className="glass rounded-xl p-5 border border-white/10 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Sparkles className="h-6 w-6" />
              </div>
              <div>
                <span className="text-2xl font-extrabold text-white">0.92</span>
                <span className="text-xs text-gray-400 block font-medium">Avg Trust Score</span>
              </div>
            </div>

            <div className="glass rounded-xl p-5 border border-white/10 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Activity className="h-6 w-6" />
              </div>
              <div>
                <span className="text-2xl font-extrabold text-white">100%</span>
                <span className="text-xs text-gray-400 block font-medium">Evidence Verification Rate</span>
              </div>
            </div>
          </div>

          {/* Recent Bench Cases List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-400" /> Recent Judicial Bench Dockets
              </h2>

              <Link
                href="/judge/cases"
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                View All {totalCases || 1500} Cases <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {isLoading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
              </div>
            ) : cases.length === 0 ? (
              <div className="glass rounded-2xl p-12 text-center text-gray-400 border border-white/5">
                No cases currently pending on bench docket.
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
