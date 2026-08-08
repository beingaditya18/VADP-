"use client";

import React, { useState, useEffect } from "react";
import type { ContractEvent } from "@/types/vadp";
import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from "@/types/vadp";
import { useVADP } from "@/hooks/use-vadp";
import { Clock, Shield, Key, FileText, Cpu, CheckCircle, Scale, UserCheck, Lock, Loader2 } from "lucide-react";

interface ProvenanceTimelineProps {
  events?: ContractEvent[];
  contractId?: string;
}

export const ProvenanceTimeline: React.FC<ProvenanceTimelineProps> = ({
  events: initialEvents,
  contractId,
}) => {
  const { getTimeline, loading } = useVADP();
  const [events, setEvents] = useState<ContractEvent[]>(initialEvents || []);

  useEffect(() => {
    if (initialEvents && initialEvents.length > 0) {
      setEvents(initialEvents);
    } else if (contractId) {
      getTimeline(contractId).then((res) => {
        if (res && res.length > 0) setEvents(res);
      });
    }
  }, [initialEvents, contractId, getTimeline]);
  if (!events || events.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 text-center text-slate-400 text-xs">
        No provenance timeline events recorded.
      </div>
    );
  }

  const sortedEvents = [...events].sort((a, b) => a.event_order - b.event_order);

  const getEventIcon = (type: string) => {
    switch (type) {
      case "authorization":
        return <Lock className="w-3.5 h-3.5" />;
      case "evidence_retrieval":
        return <FileText className="w-3.5 h-3.5" />;
      case "rag_query":
        return <Cpu className="w-3.5 h-3.5" />;
      case "llm_generation":
        return <Scale className="w-3.5 h-3.5" />;
      case "shap_computation":
        return <Cpu className="w-3.5 h-3.5" />;
      case "trust_risk_scoring":
        return <Shield className="w-3.5 h-3.5" />;
      case "contract_creation":
        return <Key className="w-3.5 h-3.5" />;
      case "digital_signature":
        return <Key className="w-3.5 h-3.5" />;
      case "merkle_inclusion":
        return <CheckCircle className="w-3.5 h-3.5" />;
      case "human_review":
        return <UserCheck className="w-3.5 h-3.5" />;
      case "finalization":
        return <CheckCircle className="w-3.5 h-3.5" />;
      default:
        return <Clock className="w-3.5 h-3.5" />;
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-base font-semibold text-slate-100">Decision Provenance Timeline</h3>
        <span className="text-xs text-slate-400 font-mono">
          {sortedEvents.length} Sequential Lifecycle Events
        </span>
      </div>

      <div className="relative border-l-2 border-slate-800 ml-3.5 space-y-6 my-2">
        {sortedEvents.map((evt) => {
          const color = EVENT_TYPE_COLORS[evt.event_type] || "#64748b";
          const label = EVENT_TYPE_LABELS[evt.event_type] || evt.event_type;

          return (
            <div key={evt.id} className="relative pl-6 group">
              {/* Event node */}
              <div
                className="absolute -left-[15px] top-0.5 w-7 h-7 rounded-full flex items-center justify-center text-white border-2 border-slate-900 shadow-md transition-transform group-hover:scale-110"
                style={{ backgroundColor: color }}
              >
                {getEventIcon(evt.event_type)}
              </div>

              {/* Event Card */}
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 hover:border-slate-700 transition-colors">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-slate-200">{label}</span>
                  <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
                    {evt.duration_ms && <span>{evt.duration_ms}ms</span>}
                    <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Event Data Payload Summary */}
                <div className="text-xs font-mono text-slate-400 bg-slate-900/90 p-2 rounded border border-slate-800/60 overflow-x-auto">
                  {Object.entries(evt.event_data).map(([k, v]) => (
                    <div key={k} className="truncate">
                      <span className="text-slate-500">{k}:</span>{" "}
                      <span className="text-indigo-300">
                        {typeof v === "object" ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Hash Chain Footer */}
                <div className="mt-2 pt-1.5 border-t border-slate-900 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span className="truncate max-w-[200px]" title={evt.event_hash}>
                    Hash: {evt.event_hash.substring(0, 16)}...
                  </span>
                  {evt.parent_hash && (
                    <span className="truncate max-w-[200px]" title={evt.parent_hash}>
                      Parent: {evt.parent_hash.substring(0, 16)}...
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
