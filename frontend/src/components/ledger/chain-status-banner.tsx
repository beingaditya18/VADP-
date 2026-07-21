"use client";

import { ShieldCheck, AlertTriangle, RefreshCw, Loader2 } from "lucide-react";
import type { ChainVerificationResult } from "@/types/ledger";

interface ChainStatusBannerProps {
  result: ChainVerificationResult | null;
  onVerify: () => void;
  isVerifying: boolean;
}

export function ChainStatusBanner({ result, onVerify, isVerifying }: ChainStatusBannerProps) {
  if (!result) {
    return (
      <div className="glass rounded-2xl p-6 border border-white/10 flex items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-white text-base">Audit Ledger Verification</h3>
          <p className="text-xs text-gray-400">Run cryptographic audit to verify SHA-256 chain and ECDSA signatures.</p>
        </div>
        <button
          onClick={onVerify}
          disabled={isVerifying}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg hover:bg-indigo-500 disabled:opacity-50"
        >
          {isVerifying ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Run Chain Audit
        </button>
      </div>
    );
  }

  return (
    <div
      className={`rounded-2xl p-6 border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl ${
        result.is_valid
          ? "bg-emerald-950/20 border-emerald-500/30"
          : "bg-red-950/20 border-red-500/30"
      }`}
    >
      <div className="flex items-start gap-4">
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-xl border flex-shrink-0 ${
            result.is_valid
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : "bg-red-500/10 border-red-500/20 text-red-400"
          }`}
        >
          {result.is_valid ? <ShieldCheck className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
        </div>

        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h3 className="font-bold text-white text-lg">
              {result.is_valid ? "Audit Chain Intact & Verified" : "TAMPERING DETECTED IN LEDGER"}
            </h3>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-300">
              {result.verified_blocks} / {result.total_blocks} Blocks Valid
            </span>
          </div>

          <p className="text-xs text-gray-300">{result.details}</p>

          <p className="text-[10px] font-mono text-gray-500">
            Forensic audit execution time: {result.verification_time_ms.toFixed(2)} ms
          </p>
        </div>
      </div>

      <button
        onClick={onVerify}
        disabled={isVerifying}
        className="flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-xs font-semibold text-white border border-white/10 hover:bg-white/20 disabled:opacity-50 flex-shrink-0"
      >
        {isVerifying ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
        Re-verify Chain
      </button>
    </div>
  );
}
