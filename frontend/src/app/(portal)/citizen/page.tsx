"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { CaseCard } from "@/components/cases/case-card";
import { useCases } from "@/hooks/use-cases";
import { useAuth } from "@/hooks/use-auth";
import { Plus, Briefcase, FileCheck, Clock, ShieldCheck, LogOut, Loader2 } from "lucide-react";

export default function CitizenDashboard() {
  const { user, logout } = useAuth();
  const { cases, totalCases, isLoading, fetchCases } = useCases();

  useEffect(() => {
    fetchCases({ page: 1 });
  }, [fetchCases]);

  return (
    <AuthGuard allowedRoles={["citizen", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Navigation Bar */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <span className="font-bold tracking-tight text-lg text-white">Citizen Portal</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400">
                Logged in as <strong className="text-white">{user?.full_name}</strong>
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

        {/* Dashboard Content */}
        <main className="mx-auto max-w-7xl px-6 py-10 space-y-8">
          {/* Header Banner */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass rounded-2xl p-8 border border-white/10">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">
                Welcome back, {user?.full_name}
              </h1>
              <p className="text-sm text-gray-400">
                Track your legal filings, monitor hearing status, and manage evidence.
              </p>
            </div>

            <Link
              href="/citizen/cases/new"
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:brightness-110 transition-all"
            >
              <Plus className="h-4 w-4" /> File New Case
            </Link>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card p-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Briefcase className="h-6 w-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{totalCases}</p>
                <p className="text-xs text-gray-400">Total Filings</p>
              </div>
            </div>

            <div className="card p-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Clock className="h-6 w-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {cases.filter((c) => c.status === "under_review" || c.status === "hearing").length}
                </p>
                <p className="text-xs text-gray-400">Active Hearings</p>
              </div>
            </div>

            <div className="card p-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <FileCheck className="h-6 w-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {cases.filter((c) => c.status === "judgment" || c.status === "closed").length}
                </p>
                <p className="text-xs text-gray-400">Disposed Cases</p>
              </div>
            </div>
          </div>

          {/* Recent Cases Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white">Recent Case Filings</h2>
              <Link href="/citizen/cases" className="text-xs font-semibold text-indigo-400 hover:underline">
                View All Cases
              </Link>
            </div>

            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
              </div>
            ) : cases.length === 0 ? (
              <div className="glass rounded-2xl p-12 text-center text-gray-400 border border-white/5 space-y-3">
                <p className="text-sm">No cases filed yet.</p>
                <Link
                  href="/citizen/cases/new"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:underline"
                >
                  <Plus className="h-3.5 w-3.5" /> Click here to file your first case
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {cases.slice(0, 6).map((caseObj) => (
                  <CaseCard key={caseObj.id} caseObj={caseObj} />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
