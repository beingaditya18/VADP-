"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useVADP } from "@/hooks/use-vadp";
import type { VerificationContract } from "@/types/vadp";
import { VerificationContractViewer } from "@/components/vadp/verification-contract-viewer";
import { ShieldCheck, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function JudgeCaseVerificationPage() {
  const params = useParams();
  const caseId = params?.id as string;
  const { getContractsForCase, loading } = useVADP();
  const [contracts, setContracts] = useState<VerificationContract[]>([]);

  useEffect(() => {
    if (caseId) {
      getContractsForCase(caseId).then(setContracts);
    }
  }, [caseId, getContractsForCase]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <Link
            href={`/judge/cases`}
            className="p-2 text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-slate-100 flex items-center">
              <ShieldCheck className="w-5 h-5 text-indigo-400 mr-2" />
              Case Verification Contracts
            </h1>
            <p className="text-xs text-slate-400 font-mono">Case ID: {caseId}</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">
          Loading Verification Contracts...
        </div>
      ) : contracts.length > 0 ? (
        <div className="space-y-6">
          {contracts.map((c) => (
            <VerificationContractViewer key={c.id} contract={c} defaultExpanded={true} />
          ))}
        </div>
      ) : (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-12 text-center text-slate-400 text-sm">
          No Verification Contracts generated for this case yet. Contracts are auto-generated when an AI analysis is performed.
        </div>
      )}
    </div>
  );
}
