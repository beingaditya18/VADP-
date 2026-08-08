"use client";

import React, { useState, useEffect } from "react";
import type { VerificationContract } from "@/types/vadp";
import { useVADP } from "@/hooks/use-vadp";
import { ContractIntegrityPanel } from "./contract-integrity-panel";
import { CompletenessChecklist } from "./completeness-checklist";
import { ProvenanceTimeline } from "./provenance-timeline";
import { CitationVerificationPanel } from "./citation-verification-panel";
import { EvidenceProvenanceGraph } from "./evidence-provenance-graph";
import { HumanReviewPanel } from "./human-review-panel";
import { ContractExportButton } from "./contract-export-button";
import { VerificationBadge } from "./verification-badge";
import { ShieldCheck, Layers, FileCode2, Clock, CheckCircle2, ChevronDown, ChevronUp, Loader2, FileX } from "lucide-react";

interface VerificationContractViewerProps {
  contract?: VerificationContract;
  contractId?: string;
  defaultExpanded?: boolean;
}

export const VerificationContractViewer: React.FC<VerificationContractViewerProps> = ({
  contract: initialContract,
  contractId,
  defaultExpanded = true,
}) => {
  const { getContractsForCase, loading: vadpLoading } = useVADP();
  const [contract, setContract] = useState<VerificationContract | undefined>(initialContract);
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [activeTab, setActiveTab] = useState<"overview" | "timeline" | "evidence" | "citations" | "raw">("overview");

  useEffect(() => {
    if (initialContract) {
      setContract(initialContract);
    } else if (contractId) {
      getContractsForCase(contractId).then((res) => {
        if (res && res.length > 0) {
          setContract(res[0]);
        }
      });
    }
  }, [initialContract, contractId, getContractsForCase]);

  if (!contract) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-400">
        {vadpLoading ? (
          <div className="flex flex-col items-center justify-center space-y-2">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            <p className="text-xs">Loading Verification Contract...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-2">
            <FileX className="w-8 h-8 text-slate-600 mb-1" />
            <p className="text-sm font-semibold text-slate-300">No Verification Contract Loaded</p>
            <p className="text-xs text-slate-500 max-w-sm">
              Verification contracts are automatically generated upon AI recommendation synthesis.
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl transition-all">
      {/* Header Bar */}
      <div className="p-4 sm:p-5 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shadow-inner">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-slate-100 tracking-tight">Verification Contract</h2>
              <VerificationBadge contract={contract} size="sm" />
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Contract ID: {contract.id} • Version {contract.contract_version}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <ContractExportButton contract={contract} />
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-5 space-y-6">
          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 space-x-2 text-xs font-medium">
            <button
              onClick={() => setActiveTab("overview")}
              className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center ${
                activeTab === "overview"
                  ? "border-indigo-500 text-indigo-400 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5 mr-1.5" />
              Overview & Integrity
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center ${
                activeTab === "timeline"
                  ? "border-indigo-500 text-indigo-400 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Clock className="w-3.5 h-3.5 mr-1.5" />
              Decision Timeline ({contract.events?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("evidence")}
              className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center ${
                activeTab === "evidence"
                  ? "border-indigo-500 text-indigo-400 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
              Evidence Provenance ({contract.evidence_count})
            </button>
            <button
              onClick={() => setActiveTab("citations")}
              className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center ${
                activeTab === "citations"
                  ? "border-indigo-500 text-indigo-400 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
              RAG Citations ({contract.rag_provenance?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("raw")}
              className={`pb-2.5 px-3 border-b-2 transition-colors flex items-center ${
                activeTab === "raw"
                  ? "border-indigo-500 text-indigo-400 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileCode2 className="w-3.5 h-3.5 mr-1.5" />
              Raw Artifact JSON
            </button>
          </div>

          {/* Tab Contents */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <ContractIntegrityPanel contract={contract} />
              <CompletenessChecklist completeness={contract.completeness} />
              <HumanReviewPanel contract={contract} onReviewSubmitted={setContract} />
            </div>
          )}

          {activeTab === "timeline" && (
            <ProvenanceTimeline events={contract.events} />
          )}

          {activeTab === "evidence" && (
            <EvidenceProvenanceGraph
              evidence={contract.evidence_provenance}
              verifiedCount={contract.evidence_verified}
              totalCount={contract.evidence_count}
            />
          )}

          {activeTab === "citations" && (
            <CitationVerificationPanel
              citations={contract.rag_provenance}
              metadata={contract.rag_metadata}
            />
          )}

          {activeTab === "raw" && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-indigo-300 max-h-96 overflow-y-auto">
              <pre>{JSON.stringify(contract, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
