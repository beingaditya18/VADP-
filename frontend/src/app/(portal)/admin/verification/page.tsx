"use client";

import React, { useEffect, useState } from "react";
import { useVADP } from "@/hooks/use-vadp";
import type { VerificationContract } from "@/types/vadp";
import { VerificationContractViewer } from "@/components/vadp/verification-contract-viewer";
import { ShieldCheck, Search, Filter, RefreshCw, FileText } from "lucide-react";

export default function VerificationExplorerPage() {
  const { getContractsForCase, loading, error } = useVADP();
  const [contracts, setContracts] = useState<VerificationContract[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCaseId, setSelectedCaseId] = useState("");

  const handleFetch = async (caseId: string) => {
    if (!caseId.trim()) return;
    const res = await getContractsForCase(caseId);
    setContracts(res);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100">Verification Contract Explorer</h1>
              <p className="text-sm text-slate-400">
                Audit and independently verify VADP decision assurance contracts
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Case Search Bar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
            placeholder="Enter Case ID to explore Verification Contracts..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <button
          onClick={() => handleFetch(selectedCaseId)}
          disabled={loading || !selectedCaseId}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg transition-colors flex items-center justify-center disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Fetch Contracts
        </button>
      </div>

      {/* Contracts List */}
      {contracts.length > 0 ? (
        <div className="space-y-6">
          {contracts.map((contract) => (
            <VerificationContractViewer key={contract.id} contract={contract} defaultExpanded={true} />
          ))}
        </div>
      ) : (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
          <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">No Verification Contracts Loaded</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
            Enter a Case ID above to query and inspect all bound VADP cryptographic verification contracts.
          </p>
        </div>
      )}
    </div>
  );
}
