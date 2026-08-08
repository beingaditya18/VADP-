"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { CaseCard } from "@/components/cases/case-card";
import { useCases } from "@/hooks/use-cases";
import { useAuth } from "@/hooks/use-auth";
import { Scale, ArrowLeft, Search, Filter, Loader2, LogOut, Plus } from "lucide-react";

export default function LawyerCasesPage() {
  const { user, logout } = useAuth();
  const { cases, totalCases, isLoading, fetchCases } = useCases();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    fetchCases({ page: 1 });
  }, [fetchCases]);

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.case_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.case_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <AuthGuard allowedRoles={["lawyer", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Header */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/lawyer" className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Scale className="h-5 w-5" />
              </Link>
              <span className="font-bold tracking-tight text-lg text-white">Advocate Representation Dockets</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400">
                Advocate <strong className="text-white">{user?.full_name}</strong>
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
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <Link href="/lawyer" className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white mb-2 transition-colors">
                <ArrowLeft className="h-4 w-4" /> Back to Advocate Portal
              </Link>
              <h1 className="text-2xl font-bold text-white mb-1">Active Filings &amp; Representation ({totalCases})</h1>
              <p className="text-xs text-gray-400">
                Manage all petitions under legal representation, submit pleadings, and track hearings.
              </p>
            </div>

            <Link
              href="/citizen/cases/new"
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:brightness-110 transition-all self-start md:self-auto"
            >
              <Plus className="h-4 w-4" /> File Petition
            </Link>
          </div>

          {/* Search & Filter Bar */}
          <div className="glass rounded-xl p-4 border border-white/10 flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="h-4 w-4 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by case title, case number, or legal area..."
                className="w-full bg-black/40 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="under_review">Under Review</option>
                <option value="hearing">Hearing Scheduled</option>
                <option value="judgment">Judgment</option>
                <option value="closed">Closed</option>
              </select>
            </div>
          </div>

          {/* Case Grid */}
          {isLoading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            </div>
          ) : filteredCases.length === 0 ? (
            <div className="glass rounded-2xl p-12 text-center text-gray-400 border border-white/5">
              No representation filings matched your search filter.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredCases.map((caseObj) => (
                <CaseCard key={caseObj.id} caseObj={caseObj} hrefPrefix="/citizen/cases" />
              ))}
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
