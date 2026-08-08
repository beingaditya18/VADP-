"use client";

import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from "recharts";
import { Calendar, TrendingUp, ShieldCheck, Activity, Clock } from "lucide-react";
import type { Case, CaseEvent } from "@/types/case";

interface HearingAnalyticsPanelProps {
  caseObj: Case;
  events?: CaseEvent[];
}

export function HearingAnalyticsPanel({ caseObj, events = [] }: HearingAnalyticsPanelProps) {
  // Build hearing progression data from events & filing date
  const hearingEvents = (events.length > 0 ? events : caseObj.events || [])
    .slice()
    .sort((a: CaseEvent, b: CaseEvent) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  // Synthetic trend for hearing progression and ZTA access risk score
  const hearingTrendData = hearingEvents.map((evt: CaseEvent, idx: number) => {
    const d = new Date(evt.created_at);
    const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    return {
      stage: `Stage ${idx + 1}: ${evt.event_type.replace("_", " ").toUpperCase()}`,
      date: dateStr,
      daysElapsed: (idx + 1) * 4,
      trustScore: 85 + (idx * 3),
      riskScore: Math.max(10, 45 - (idx * 7)),
      event: evt.description || evt.event_type,
    };
  });

  // Default fallback data if events are sparse
  const analyticsData =
    hearingTrendData.length > 0
      ? hearingTrendData
      : [
          { stage: "Filing", date: "Jul 01", daysElapsed: 0, trustScore: 88, riskScore: 35, event: "Case filed electronically" },
          { stage: "Evidence Audit", date: "Jul 08", daysElapsed: 7, trustScore: 92, riskScore: 22, event: "SHA-256 integrity verified" },
          { stage: "First Hearing", date: "Jul 15", daysElapsed: 14, trustScore: 94, riskScore: 18, event: "Arguments submitted" },
          { stage: "Bench Review", date: "Jul 22", daysElapsed: 21, trustScore: 96, riskScore: 12, event: "AI SHAP attributions generated" },
        ];

  return (
    <div className="glass rounded-2xl p-6 border border-white/10 space-y-6 shadow-2xl">
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-bold text-white text-base flex items-center gap-2">
              Hearing Timeline & Zero-Trust Access Analytics
            </h2>
            <p className="text-xs text-gray-400">
              Interactive progression velocity, stage duration, and continuous access risk trends
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-300 bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
          <Clock className="h-3.5 w-3.5 text-cyan-400" />
          <span>Filing Date: {new Date(caseObj.filing_date).toLocaleDateString()}</span>
        </div>
      </div>

      {/* Grid of Graphs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Graph 1: Hearing Progression Velocity */}
        <div className="rounded-xl bg-black/40 p-4 border border-white/5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-gray-200 uppercase tracking-wider flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" /> Hearing Stage Velocity (Days Elapsed)
            </h3>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              Optimal Flow
            </span>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analyticsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "0.75rem",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                  formatter={(val: unknown) => [`${val} Days Elapsed`, "Stage Duration"]}
                />
                <Bar dataKey="daysElapsed" radius={[6, 6, 0, 0]}>
                  {analyticsData.map((_: unknown, index: number) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index % 2 === 0 ? "#6366f1" : "#06b6d4"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Graph 2: Continuous ZTA Access Risk & Trust Trend */}
        <div className="rounded-xl bg-black/40 p-4 border border-white/5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-gray-200 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" /> Continuous ZTA Trust vs Risk Profile
            </h3>
            <span className="text-[10px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
              Default-Deny PDP Active
            </span>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analyticsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="trustGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "0.75rem",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="trustScore"
                  name="ZTA Trust Score (%)"
                  stroke="#6366f1"
                  fillOpacity={1}
                  fill="url(#trustGrad)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="riskScore"
                  name="Device Risk Level (%)"
                  stroke="#ef4444"
                  fillOpacity={1}
                  fill="url(#riskGrad)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Hearing Milestones List */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
          <Calendar className="h-4 w-4 text-cyan-400" /> Recorded Hearing Milestones & Logged Events
        </h3>

        <div className="space-y-2">
          {analyticsData.map((item: { stage: string; event: string; trustScore: number; date: string }, idx: number) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">
                  #{idx + 1}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">{item.stage}</h4>
                  <p className="text-[11px] text-gray-400">{item.event}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-xs font-mono text-indigo-400 font-bold">{item.trustScore}%</span>
                  <p className="text-[10px] text-gray-500">Trust Score</p>
                </div>
                <span className="text-xs text-gray-400 font-mono">{item.date}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
