"use client";

import { ShieldCheck, Award } from "lucide-react";
import type { TrustScoreBreakdown } from "@/types/ai";

interface TrustScoreGaugeProps {
  trustBreakdown: TrustScoreBreakdown;
}

export function TrustScoreGauge({ trustBreakdown }: TrustScoreGaugeProps) {
  if (!trustBreakdown) return null;

  const scorePercent = Math.round(trustBreakdown.overall * 100);

  return (
    <div className="card card-glow p-6 space-y-4 border border-white/10">
      <div className="flex items-center justify-between border-b border-white/5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Award className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Formal Trust Score</h3>
            <p className="text-xs text-gray-400">α·S_model + β·S_evidence + γ·S_source + δ·S_consistency</p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-3xl font-extrabold text-emerald-400 font-mono">{scorePercent}%</span>
          <span className="block text-[10px] uppercase tracking-wider text-gray-400 font-semibold">Overall Trust</span>
        </div>
      </div>

      {/* Sub-factor Breakdown Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div className="rounded-xl bg-white/5 p-3 border border-white/5 space-y-1">
          <span className="text-gray-400 text-[10px] uppercase font-semibold block">α (35%) Model Conf.</span>
          <span className="text-white font-mono font-bold text-sm">{(trustBreakdown.model_confidence * 100).toFixed(0)}%</span>
        </div>

        <div className="rounded-xl bg-white/5 p-3 border border-white/5 space-y-1">
          <span className="text-gray-400 text-[10px] uppercase font-semibold block">β (35%) Evidence Qual.</span>
          <span className="text-emerald-400 font-mono font-bold text-sm">{(trustBreakdown.evidence_quality * 100).toFixed(0)}%</span>
        </div>

        <div className="rounded-xl bg-white/5 p-3 border border-white/5 space-y-1">
          <span className="text-gray-400 text-[10px] uppercase font-semibold block">γ (15%) Source Reliab.</span>
          <span className="text-cyan-400 font-mono font-bold text-sm">{(trustBreakdown.source_reliability * 100).toFixed(0)}%</span>
        </div>

        <div className="rounded-xl bg-white/5 p-3 border border-white/5 space-y-1">
          <span className="text-gray-400 text-[10px] uppercase font-semibold block">δ (15%) Consistency</span>
          <span className="text-indigo-400 font-mono font-bold text-sm">{(trustBreakdown.consistency * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
