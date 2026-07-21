"use client";

import { AlertTriangle, ShieldCheck, Info } from "lucide-react";
import type { RiskAssessment } from "@/types/ai";

interface RiskLevelBadgeProps {
  assessment: RiskAssessment;
}

export function RiskLevelBadge({ assessment }: RiskLevelBadgeProps) {
  if (!assessment) return null;

  const scorePercent = Math.round(assessment.overall_score * 100);

  const getRiskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "critical":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      case "high":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "medium":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    }
  };

  const badgeStyle = getRiskColor(assessment.risk_level);

  return (
    <div className="card card-glow p-6 space-y-4 border border-white/10">
      <div className="flex items-center justify-between border-b border-white/5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Multi-Factor Risk Assessment</h3>
            <p className="text-xs text-gray-400">Security, evidence gap, and case priority risk scoring</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${badgeStyle}`}>
            {assessment.risk_level} Risk
          </span>
          <span className="text-2xl font-bold font-mono text-white">{scorePercent}%</span>
        </div>
      </div>

      {/* Feature Contributions */}
      {assessment.features && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {assessment.features.map((feat, idx) => (
            <div key={idx} className="rounded-xl bg-white/5 p-3 border border-white/5 flex items-center justify-between">
              <span className="text-gray-300 font-medium">{feat.name}</span>
              <span className="font-mono text-gray-400 font-semibold">
                +{(feat.contribution * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
