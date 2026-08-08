"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { SHAPVisualizer } from "@/components/ai/shap-visualizer";
import { TrustScoreGauge } from "@/components/ai/trust-score-gauge";
import { RiskLevelBadge } from "@/components/ai/risk-level-badge";
import { HearingAnalyticsPanel } from "@/components/cases/hearing-analytics-panel";
import { EvidenceVaultPanel } from "@/components/evidence/evidence-vault-panel";
import { useAI } from "@/hooks/use-ai";
import { useCases } from "@/hooks/use-cases";
import { useAuth } from "@/hooks/use-auth";
import { Scale, ArrowLeft, Loader2, Sparkles, LogOut, FileText } from "lucide-react";

export default function CitizenCaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;

  const { user, logout } = useAuth();
  const { currentAnalysis, isLoading, analyzeCase } = useAI();
  const { selectedCase, fetchCaseById } = useCases();

  useEffect(() => {
    if (caseId) {
      fetchCaseById(caseId);
      analyzeCase(caseId);
    }
  }, [caseId, fetchCaseById, analyzeCase]);

  return (
    <AuthGuard allowedRoles={["citizen", "lawyer", "judge", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Navigation Header */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/citizen" className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Scale className="h-5 w-5" />
              </Link>
              <span className="font-bold tracking-tight text-lg text-white">Citizen Docket Detail Portal</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400">
                Logged in as <strong className="text-white">{user?.full_name}</strong> ({user?.role})
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

        {/* Content */}
        <main className="mx-auto max-w-7xl px-6 py-10 space-y-8">
          <Link href="/citizen" className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="h-4 w-4" /> Back to My Filings
          </Link>

          {/* Header Title */}
          <div className="glass rounded-2xl p-8 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20">
                  {selectedCase?.case_number || "Case Docket"}
                </span>
                <span className="text-xs font-semibold uppercase px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-gray-300">
                  {selectedCase?.case_type || "Civil"}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-white mb-1">
                {selectedCase?.title || "Judicial Case Details"}
              </h1>
              <p className="text-xs text-gray-400">
                Verified Zero Trust Evidence, SHA-256 Chain of Custody &amp; Hearing Timeline Analytics
              </p>
            </div>

            {selectedCase && (
              <span className="text-xs font-bold uppercase px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                {selectedCase.status.replace("_", " ")}
              </span>
            )}
          </div>

          {isLoading || !selectedCase ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
              <p className="text-sm text-gray-400">Fetching case records, evidence hashes &amp; hearing analytics...</p>
            </div>
          ) : (
            <div className="space-y-8 animate-fade-in">
              {/* Hearing Timeline & Stage Velocity Recharts Analytics */}
              <HearingAnalyticsPanel caseObj={selectedCase} events={selectedCase.events} />

              {/* Zero-Trust Evidence Vault & SHA-256 Chain of Custody */}
              <EvidenceVaultPanel caseId={caseId} />

              {/* AI Summary & SHAP Attributions (if available) */}
              {currentAnalysis && (
                <>
                  <div className="glass rounded-2xl p-6 border border-white/10 space-y-4 shadow-xl">
                    <div className="flex items-center gap-2 border-b border-white/5 pb-3">
                      <Sparkles className="h-5 w-5 text-indigo-400" />
                      <h2 className="font-bold text-white text-base">Legal Case Summary &amp; SHAP Explainability</h2>
                    </div>

                    <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap rounded-xl bg-black/40 p-5 border border-white/5 font-sans">
                      {currentAnalysis.summary}
                    </div>
                  </div>

                  {currentAnalysis.recommendation?.explanations?.[0]?.shap_values && (
                    <SHAPVisualizer shapValues={currentAnalysis.recommendation.explanations[0].shap_values} />
                  )}
                </>
              )}
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
