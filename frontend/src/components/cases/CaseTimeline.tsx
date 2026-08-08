"use client";

import React, { useState } from "react";
import {
  Calendar,
  FileText,
  ShieldCheck,
  Gavel,
  Clock,
  Filter,
  CheckCircle,
  AlertCircle,
  ChevronRight,
} from "lucide-react";

export interface CaseTimelineNode {
  id: string;
  timestamp: string;
  milestone_type: "FILING" | "EVIDENCE" | "HEARING" | "RULING" | "EVENT";
  title: string;
  description: string;
  actor_id?: string;
  badge_color?: string;
  metadata?: Record<string, any>;
}

interface CaseTimelineProps {
  timeline: CaseTimelineNode[];
  caseNumber: string;
}

export const CaseTimeline: React.FC<CaseTimelineProps> = ({ timeline, caseNumber }) => {
  const [filterType, setFilterType] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filteredTimeline = filterType === "ALL"
    ? timeline
    : timeline.filter((node) => node.milestone_type === filterType);

  const getMilestoneIcon = (type: string) => {
    switch (type) {
      case "FILING":
        return <FileText className="w-4 h-4 text-blue-400" />;
      case "EVIDENCE":
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
      case "HEARING":
        return <Clock className="w-4 h-4 text-indigo-400" />;
      case "RULING":
        return <Gavel className="w-4 h-4 text-purple-400" />;
      default:
        return <Calendar className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-indigo-400" />
            Case Lifecycle Milestone Timeline ({caseNumber})
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological audit trail of filings, evidence logs, hearings, and judicial orders.
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-slate-950/60 p-1 border border-slate-800 rounded-xl">
          <Filter className="w-3.5 h-3.5 text-slate-400 ml-2" />
          {["ALL", "FILING", "EVIDENCE", "HEARING", "EVENT"].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                filterType === type
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="relative pl-6 border-l-2 border-slate-800 space-y-6">
        {filteredTimeline.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No milestones found for selected filter.
          </div>
        ) : (
          filteredTimeline.map((node) => {
            const isExpanded = expandedId === node.id;
            const dateStr = new Date(node.timestamp).toLocaleString("en-US", {
              dateStyle: "medium",
              timeStyle: "short",
            });

            return (
              <div key={node.id} className="relative group">
                {/* Bullet Node */}
                <div className="absolute -left-[31px] top-1 p-1.5 bg-slate-900 border-2 border-slate-700 rounded-full group-hover:border-indigo-500 transition-colors">
                  {getMilestoneIcon(node.milestone_type)}
                </div>

                {/* Card Container */}
                <div
                  onClick={() => setExpandedId(isExpanded ? null : node.id)}
                  className="bg-slate-950/50 border border-slate-800/80 hover:border-indigo-500/50 rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg hover:shadow-indigo-500/5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider text-white ${node.badge_color || "bg-indigo-600"}`}>
                        {node.milestone_type}
                      </span>
                      <h4 className="text-sm font-semibold text-slate-200">{node.title}</h4>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
                      <span>{dateStr}</span>
                      <ChevronRight className={`w-4 h-4 transition-transform ${isExpanded ? "rotate-90 text-indigo-400" : ""}`} />
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                    {node.description}
                  </p>

                  {/* Expanded Metadata Details */}
                  {isExpanded && node.metadata && Object.keys(node.metadata).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-800/60 bg-slate-900/60 p-3 rounded-lg text-xs font-mono text-slate-300 space-y-1 animate-in fade-in duration-150">
                      <span className="text-[10px] uppercase text-indigo-400 font-bold block mb-1">Audit Ledger Metadata</span>
                      {Object.entries(node.metadata).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="text-slate-500 capitalize">{k.replace("_", " ")}:</span>
                          <span className="text-slate-200">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
