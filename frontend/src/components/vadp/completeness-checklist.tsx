"use client";

import React from "react";
import type { CompletenessInvariant } from "@/types/vadp";
import { COMPLETENESS_LABELS } from "@/types/vadp";
import { CheckCircle2, Circle, AlertCircle } from "lucide-react";

interface CompletenessChecklistProps {
  completeness: CompletenessInvariant;
}

export const CompletenessChecklist: React.FC<CompletenessChecklistProps> = ({ completeness }) => {
  const criteriaKeys = [
    "has_authorization",
    "has_evidence",
    "has_rag_citations",
    "has_shap_explanation",
    "has_trust_score",
    "has_risk_assessment",
    "has_digital_signature",
    "has_merkle_inclusion",
    "has_human_review",
  ] as const;

  const satisfiedCount = criteriaKeys.filter((k) => completeness[k]).length;
  const percentage = Math.round((satisfiedCount / criteriaKeys.length) * 100);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-base font-semibold text-slate-100">Completeness Invariant</h3>
          <p className="text-xs text-slate-400">
            VADP criteria required for binding contract finalization
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
              completeness.overall_complete
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : "bg-amber-500/10 text-amber-400 border-amber-500/30"
            }`}
          >
            {satisfiedCount} / {criteriaKeys.length} Criteria ({percentage}%)
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-slate-950 h-2 rounded-full mb-4 overflow-hidden border border-slate-800">
        <div
          className={`h-full transition-all duration-500 ${
            completeness.overall_complete ? "bg-emerald-500" : "bg-indigo-500"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Checklist grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {criteriaKeys.map((key) => {
          const isSatisfied = completeness[key];
          const label = COMPLETENESS_LABELS[key] || key;

          return (
            <div
              key={key}
              className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-medium transition-colors ${
                isSatisfied
                  ? "bg-slate-950/40 border-slate-800 text-slate-200"
                  : "bg-amber-950/10 border-amber-500/20 text-amber-300"
              }`}
            >
              <div className="flex items-center space-x-2 truncate">
                {isSatisfied ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <Circle className="w-4 h-4 text-amber-400 shrink-0" />
                )}
                <span className="truncate">{label}</span>
              </div>
              <span
                className={`text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded ${
                  isSatisfied
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-amber-500/10 text-amber-400"
                }`}
              >
                {isSatisfied ? "Pass" : "Missing"}
              </span>
            </div>
          );
        })}
      </div>

      {completeness.missing_components.length > 0 && (
        <div className="mt-3.5 flex items-center text-xs text-amber-400 bg-amber-950/20 border border-amber-800/30 p-2.5 rounded-lg">
          <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
          <span>
            Pending criteria:{" "}
            <span className="font-semibold text-amber-300">
              {completeness.missing_components.join(", ")}
            </span>
          </span>
        </div>
      )}
    </div>
  );
};
