"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { CaseCard } from "@/components/cases/case-card";
import { useCases } from "@/hooks/use-cases";
import { useAuth } from "@/hooks/use-auth";
import { Scale, ArrowLeft, Search, Filter, Loader2, LogOut, Sparkles, ChevronLeft, ChevronRight, SlidersHorizontal } from "lucide-react";

const CATEGORIES = [
  "All Categories",
  "Criminal",
  "Civil",
  "Constitutional",
  "Administrative",
  "Environmental",
  "Intellectual Property",
  "Labour",
  "Taxation",
  "Consumer",
  "Family Law",
  "Property",
  "Commercial",
];

export default function JudgeCasesPage() {
  const { user, logout } = useAuth();
  const { cases, totalCases, totalPages, isLoading, fetchCases } = useCases();

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("All Categories");
  const [sortBy, setSortBy] = useState<string>("filing_date");
  const [sortOrder, setSortOrder] = useState<string>("desc");
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(12);

  useEffect(() => {
    fetchCases({
      search: searchTerm.trim() || undefined,
      status: statusFilter === "all" ? undefined : statusFilter,
      case_type: categoryFilter === "All Categories" ? undefined : categoryFilter,
      sort_by: sortBy,
      sort_order: sortOrder,
      page,
      page_size: pageSize,
    });
  }, [fetchCases, searchTerm, statusFilter, categoryFilter, sortBy, sortOrder, page, pageSize]);

  return (
    <AuthGuard allowedRoles={["judge", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Header */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/judge" className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Scale className="h-5 w-5" />
              </Link>
              <div>
                <span className="font-bold tracking-tight text-lg text-white block">Judicial Bench Docket Directory</span>
                <span className="text-[10px] text-indigo-400 font-mono">1500 Real ILDC Supreme Court Cases</span>
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

        {/* Main Content */}
        <main className="mx-auto max-w-7xl px-6 py-8 space-y-6">
          <div>
            <Link href="/judge" className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white mb-2 transition-colors">
              <ArrowLeft className="h-4 w-4" /> Back to Bench Portal
            </Link>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-indigo-400" /> Assigned Case Bench Docket ({totalCases})
                </h1>
                <p className="text-xs text-gray-400">
                  Browse and review all 1500 real Indian Legal Documents Corpus (ILDC) judgments backed by zero-trust RAG, SHAP explainability, and Verification Contracts.
                </p>
              </div>

              <div className="flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1.5 rounded-xl text-xs text-indigo-300 font-medium">
                <Scale className="h-4 w-4 text-indigo-400" />
                <span>1500 Real Supreme Court Records</span>
              </div>
            </div>
          </div>

          {/* Search, Filter & Sort Controls */}
          <div className="glass rounded-2xl p-5 border border-white/10 space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search Bar */}
              <div className="relative flex-1">
                <Search className="h-4 w-4 text-gray-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Search docket by case title, case number, or legal domain..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-3">
                {/* Domain Filter */}
                <div className="flex items-center gap-1.5">
                  <Filter className="h-3.5 w-3.5 text-indigo-400" />
                  <select
                    value={categoryFilter}
                    onChange={(e) => {
                      setCategoryFilter(e.target.value);
                      setPage(1);
                    }}
                    className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setPage(1);
                  }}
                  className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="all">All Docket Statuses</option>
                  <option value="under_review">Under Review</option>
                  <option value="hearing">Hearing Scheduled</option>
                  <option value="judgment">Judgment Ready</option>
                  <option value="closed">Closed / Disposed</option>
                </select>

                {/* Sort Filter */}
                <div className="flex items-center gap-1.5">
                  <SlidersHorizontal className="h-3.5 w-3.5 text-indigo-400" />
                  <select
                    value={`${sortBy}_${sortOrder}`}
                    onChange={(e) => {
                      const [sb, so] = e.target.value.split("_");
                      setSortBy(sb);
                      setSortOrder(so);
                    }}
                    className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="filing_date_desc">Newest Filing Date</option>
                    <option value="filing_date_asc">Oldest Filing Date</option>
                    <option value="case_number_asc">Case Number (A-Z)</option>
                    <option value="status_asc">Status</option>
                  </select>
                </div>

                {/* Page Size */}
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value={12}>12 per page</option>
                  <option value={24}>24 per page</option>
                  <option value={48}>48 per page</option>
                </select>
              </div>
            </div>
          </div>

          {/* Case Grid */}
          {isLoading ? (
            <div className="flex justify-center py-24">
              <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
            </div>
          ) : cases.length === 0 ? (
            <div className="glass rounded-2xl p-16 text-center text-gray-400 border border-white/5 space-y-3">
              <Scale className="h-12 w-12 text-gray-600 mx-auto" />
              <p className="text-base font-semibold text-white">No matching judicial dockets found.</p>
              <p className="text-xs text-gray-500">Try broadening your search term or domain filter criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {cases.map((c) => (
                <CaseCard key={c.id} caseObj={c} hrefPrefix="/judge/cases" />
              ))}
            </div>
          )}

          {/* Pagination Controls */}
          {!isLoading && totalCases > 0 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 glass rounded-2xl p-4 border border-white/10 text-xs text-gray-400">
              <div>
                Showing <strong className="text-white">{(page - 1) * pageSize + 1}</strong> to{" "}
                <strong className="text-white">{Math.min(page * pageSize, totalCases)}</strong> of{" "}
                <strong className="text-white">{totalCases}</strong> judicial cases
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 hover:bg-indigo-600/20 hover:border-indigo-500/40 text-white disabled:opacity-40 disabled:pointer-events-none transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" /> Previous
                </button>

                <span className="px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-semibold">
                  Page {page} of {Math.max(1, totalPages)}
                </span>

                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 hover:bg-indigo-600/20 hover:border-indigo-500/40 text-white disabled:opacity-40 disabled:pointer-events-none transition-colors"
                >
                  Next <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
