"use client";

import { TrendingUp, TrendingDown, Layers, HelpCircle } from "lucide-react";
import type { SHAPExplanation } from "@/types/ai";

interface SHAPVisualizerProps {
  shapValues: SHAPExplanation[];
}

export function SHAPVisualizer({ shapValues }: SHAPVisualizerProps) {
  if (!shapValues || shapValues.length === 0) return null;

  return (
    <div className="card card-glow p-6 space-y-5 border border-white/10">
      <div className="flex items-center justify-between border-b border-white/5 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">SHAP Explainability Visualizer</h3>
            <p className="text-xs text-gray-400">Shapley Additive exPlanations feature contribution breakdown</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <TrendingUp className="h-3.5 w-3.5" /> Supports Decision (+)
          </span>
          <span className="flex items-center gap-1.5 text-rose-400 font-semibold">
            <TrendingDown className="h-3.5 w-3.5" /> Increases Risk (-)
          </span>
        </div>
      </div>

      {/* SHAP Bars */}
      <div className="space-y-4">
        {shapValues.map((item, idx) => {
          const isPositive = item.contribution_direction === "positive" || item.shap_value >= 0;
          const absVal = Math.min(1.0, Math.abs(item.shap_value));
          const widthPercent = Math.max(10, Math.round(absVal * 100 * 2)); // Scale for visibility

          return (
            <div key={idx} className="space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-200">{item.feature_name}</span>
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-gray-400">Value: {item.feature_value}</span>
                  <span className={`font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                    {item.shap_value > 0 ? `+${item.shap_value.toFixed(3)}` : item.shap_value.toFixed(3)}
                  </span>
                </div>
              </div>

              {/* Progress bar container */}
              <div className="h-3 w-full rounded-full bg-white/5 overflow-hidden flex items-center p-0.5 border border-white/5">
                <div
                  style={{ width: `${widthPercent}%` }}
                  className={`h-full rounded-full transition-all duration-500 ${
                    isPositive
                      ? "bg-gradient-to-r from-emerald-600 to-teal-400 shadow-md shadow-emerald-500/20"
                      : "bg-gradient-to-r from-rose-600 to-red-400 shadow-md shadow-rose-500/20"
                  }`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
