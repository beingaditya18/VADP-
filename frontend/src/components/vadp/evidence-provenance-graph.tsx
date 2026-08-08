"use client";

import React from "react";
import type { EvidenceProvenanceItem } from "@/types/vadp";
import { FileCheck, AlertTriangle, Clock, ShieldCheck, Database } from "lucide-react";

interface EvidenceProvenanceGraphProps {
  evidence: EvidenceProvenanceItem[];
  verifiedCount?: number;
  totalCount?: number;
}

export const EvidenceProvenanceGraph: React.FC<EvidenceProvenanceGraphProps> = ({
  evidence,
  verifiedCount = 0,
  totalCount = 0,
}) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-semibold text-slate-100">Evidence Provenance & Hash Integrity</h3>
        </div>
        <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-full border border-cyan-500/20">
          {verifiedCount} / {totalCount || evidence.length} Verified Records
        </span>
      </div>

      {(!evidence || evidence.length === 0) ? (
        <div className="p-4 text-center text-xs text-slate-400 border border-dashed border-slate-800 rounded-lg">
          No evidence records bound to this case.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {evidence.map((item) => {
            const isVerified = item.verification_status === "verified";
            const isTampered = item.verification_status === "tampered";

            return (
              <div
                key={item.evidence_id}
                className={`p-3.5 rounded-lg border text-xs transition-colors ${
                  isVerified
                    ? "bg-slate-950/60 border-slate-800"
                    : isTampered
                    ? "bg-rose-950/20 border-rose-500/30"
                    : "bg-amber-950/10 border-amber-500/20"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-slate-200 capitalize">
                    {item.evidence_type.replace("_", " ")}
                  </span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                      isVerified
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        : isTampered
                        ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    }`}
                  >
                    {isVerified ? (
                      <ShieldCheck className="w-3 h-3 mr-1 text-emerald-400" />
                    ) : isTampered ? (
                      <AlertTriangle className="w-3 h-3 mr-1 text-rose-400" />
                    ) : (
                      <Clock className="w-3 h-3 mr-1 text-amber-400" />
                    )}
                    {item.verification_status}
                  </span>
                </div>

                <div className="space-y-1 font-mono text-[11px] text-slate-400 bg-slate-900/80 p-2 rounded border border-slate-800/60">
                  <div className="truncate">
                    <span className="text-slate-500">Hash:</span>{" "}
                    <span className="text-cyan-300" title={item.integrity_hash}>
                      {item.integrity_hash}
                    </span>
                  </div>
                  <div className="truncate text-slate-500">
                    Doc ID: {item.document_id}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
