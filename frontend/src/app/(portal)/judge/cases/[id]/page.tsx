"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { SHAPVisualizer } from "@/components/ai/shap-visualizer";
import { TrustScoreGauge } from "@/components/ai/trust-score-gauge";
import { RiskLevelBadge } from "@/components/ai/risk-level-badge";
import { useAI } from "@/hooks/use-ai";
import { useCases } from "@/hooks/use-cases";
import { useAuth } from "@/hooks/use-auth";
import { Scale, CheckCircle, XCircle, AlertTriangle, ArrowLeft, Loader2, Sparkles, LogOut, FileText } from "lucide-react";

export default function JudgeCaseAnalysisPage() {
  const params = useParams();
  const caseId = params.id as string;

  const { user, logout } = useAuth();
  const { currentAnalysis, isLoading, analyzeCase, reviewRecommendation } = useAI();
  const { selectedCase, fetchCaseById } = useCases();

  useEffect(() => {
    if (caseId) {
      fetchCaseById(caseId);
      analyzeCase(caseId);
    }
  }, [caseId, fetchCaseById, analyzeCase]);

  const handleReview = async (action: "approved" | "rejected" | "flagged") => {
    if (currentAnalysis?.recommendation?.id) {
      await reviewRecommendation(currentAnalysis.recommendation.id, action);
    }
  };

  return (
    <AuthGuard allowedRoles={["judge", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Navigation Header */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Scale className="h-5 w-5" />
              </Link>
              <span className="font-bold tracking-tight text-lg text-white">Judicial Decision Support Portal</span>
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
            <ArrowLeft className="h-4 w-4" /> Back
          </Link>

          {/* Header Title */}
          <div className="glass rounded-2xl p-8 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <span className="font-mono text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20 mb-2 inline-block">
                {selectedCase?.case_number || "Case Analysis"}
              </span>
              <h1 className="text-2xl font-bold text-white mb-1">
                {selectedCase?.title || "Judicial Case Decision Support"}
              </h1>
              <p className="text-xs text-gray-400">Explainable AI (XAI) multi-factor trust calculation & SHAP feature analysis</p>
            </div>

            {currentAnalysis?.recommendation && (
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400">Review Status:</span>
                <span className="text-xs font-bold capitalize px-3 py-1 rounded-full bg-white/10 border border-white/10 text-white">
                  {currentAnalysis.recommendation.status}
                </span>
              </div>
            )}
          </div>

          {isLoading || !currentAnalysis ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
              <p className="text-sm text-gray-400">Computing SHAP feature values & executing Trust Score formula...</p>
            </div>
          ) : (
            <div className="space-y-8 animate-fade-in">
              {/* Trust Score & Risk Assessment Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TrustScoreGauge trustBreakdown={currentAnalysis.trust_breakdown} />
                <RiskLevelBadge assessment={currentAnalysis.risk_assessment} />
              </div>

              {/* RAG Legal Summary & AI Recommendation */}
              <div className="glass rounded-2xl p-6 border border-white/10 space-y-4 shadow-xl">
                <div className="flex items-center gap-2 border-b border-white/5 pb-3">
                  <Sparkles className="h-5 w-5 text-indigo-400" />
                  <h2 className="font-bold text-white text-base">Grounded Legal Summary & Recommendation</h2>
                </div>

                <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap rounded-xl bg-black/40 p-5 border border-white/5 font-sans">
                  {currentAnalysis.summary}
                </div>
              </div>

              {/* SHAP Feature Importance Visualizer */}
              {currentAnalysis.recommendation.explanations?.[0]?.shap_values && (
                <SHAPVisualizer shapValues={currentAnalysis.recommendation.explanations[0].shap_values} />
              )}

              {/* Judge Decision Review Controls */}
              <div className="glass rounded-2xl p-6 border border-white/10 flex items-center justify-between gap-4 shadow-xl">
                <div>
                  <h3 className="font-bold text-white text-base">Judicial Review & Override Action</h3>
                  <p className="text-xs text-gray-400">Approve, reject, or flag AI recommendation for expert human review.</p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleReview("approved")}
                    className="flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-lg hover:bg-emerald-500 transition-all"
                  >
                    <CheckCircle className="h-4 w-4" /> Approve Recommendation
                  </button>

                  <button
                    onClick={() => handleReview("rejected")}
                    className="flex items-center gap-1.5 rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-lg hover:bg-rose-500 transition-all"
                  >
                    <XCircle className="h-4 w-4" /> Reject & Override
                  </button>

                  <button
                    onClick={() => handleReview("flagged")}
                    className="flex items-center gap-1.5 rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white shadow-lg hover:bg-amber-500 transition-all"
                  >
                    <AlertTriangle className="h-4 w-4" /> Flag for Review
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
