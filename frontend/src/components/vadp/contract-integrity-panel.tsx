"use client";

import React, { useState } from "react";
import type { VerificationContract, ContractVerificationResult } from "@/types/vadp";
import { useVADP } from "@/hooks/use-vadp";
import { ShieldCheck, ShieldAlert, Key, Link as LinkIcon, RefreshCw, CheckCircle2, XCircle } from "lucide-react";

interface ContractIntegrityPanelProps {
  contract: VerificationContract;
  onVerified?: (result: ContractVerificationResult) => void;
}

export const ContractIntegrityPanel: React.FC<ContractIntegrityPanelProps> = ({
  contract,
  onVerified,
}) => {
  const { verifyContract, loading } = useVADP();
  const [result, setResult] = useState<ContractVerificationResult | null>(null);

  const handleVerify = async () => {
    const res = await verifyContract(contract.id);
    if (res) {
      setResult(res);
      if (onVerified) onVerified(res);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-slate-100">Cryptographic Integrity</h3>
        </div>
        <button
          onClick={handleVerify}
          disabled={loading}
          className="inline-flex items-center px-3 py-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg transition-colors shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Verifying..." : "Verify Independent Proof"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Contract Hash */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center text-xs font-medium text-slate-400 mb-1">
            <Key className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
            Canonical Hash (SHA-256)
          </div>
          <div className="font-mono text-xs text-cyan-300 truncate" title={contract.contract_hash}>
            {contract.contract_hash}
          </div>
        </div>

        {/* Digital Signature */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center text-xs font-medium text-slate-400 mb-1">
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-purple-400" />
            Digital Signature ({contract.signing_algorithm || "ECDSA"})
          </div>
          <div className="font-mono text-xs text-purple-300 truncate" title={contract.digital_signature || "Unsigned"}>
            {contract.digital_signature || "Pending Signature"}
          </div>
        </div>

        {/* Merkle Leaf */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center text-xs font-medium text-slate-400 mb-1">
            <LinkIcon className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            Merkle Leaf Hash
          </div>
          <div className="font-mono text-xs text-emerald-300 truncate" title={contract.merkle_leaf_hash || "Unbound"}>
            {contract.merkle_leaf_hash || "Awaiting Inclusion"}
          </div>
        </div>
      </div>

      {/* Verification Result Banner */}
      {result && (
        <div
          className={`p-4 rounded-lg border ${
            result.is_valid
              ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-300"
              : "bg-rose-950/30 border-rose-500/30 text-rose-300"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center font-medium text-sm">
              {result.is_valid ? (
                <CheckCircle2 className="w-4 h-4 mr-2 text-emerald-400" />
              ) : (
                <XCircle className="w-4 h-4 mr-2 text-rose-400" />
              )}
              {result.is_valid
                ? "Verification Passed: Contract is authentic and untampered"
                : "Verification Failed: Contract integrity issue detected"}
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {result.verification_time_ms} ms
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs border-t border-slate-800/80 pt-2.5 mt-2">
            <div>
              Hash Match:{" "}
              <span className={result.hash_valid ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
                {result.hash_valid ? "Valid" : "Mismatch"}
              </span>
            </div>
            <div>
              ECDSA Signature:{" "}
              <span className={result.signature_valid ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
                {result.signature_valid ? "Valid" : "Invalid"}
              </span>
            </div>
            <div>
              Merkle Root:{" "}
              <span className={result.merkle_valid ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
                {result.merkle_valid ? "Valid" : "Invalid"}
              </span>
            </div>
            <div>
              Evidence Chain:{" "}
              <span className={result.evidence_integrity_valid ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
                {result.evidence_integrity_valid ? "Intact" : "Tampered"}
              </span>
            </div>
          </div>

          {result.failures && result.failures.length > 0 && (
            <div className="mt-2 text-xs bg-rose-950/50 p-2 rounded border border-rose-800/40 text-rose-200">
              <span className="font-semibold block mb-1">Failure Details:</span>
              <ul className="list-disc list-inside space-y-0.5 font-mono text-[11px]">
                {result.failures.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
