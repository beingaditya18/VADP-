"use client";

import React, { useState } from "react";
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, FileText, Lock } from "lucide-react";

interface JudicialOverrideModalProps {
  contractId: string;
  caseId: string;
  trustScore: number;
  riskScore: number;
  escalationReason?: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updatedContract: any) => void;
}

export const JudicialOverrideModal: React.FC<JudicialOverrideModalProps> = ({
  contractId,
  caseId,
  trustScore,
  riskScore,
  escalationReason,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [action, setAction] = useState<"APPROVED" | "REJECTED" | "OVERRIDDEN">("APPROVED");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`/api/v1/vadp/contracts/${contractId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: action,
          notes: notes,
        }),
      });

      if (!res.ok) {
        throw new Error(`Review submission failed: ${res.statusText}`);
      }

      const data = await res.json();
      onSuccess(data);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to submit judicial override decision.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl max-w-xl w-full p-6 text-slate-100">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-6 h-6 text-amber-400" />
            <h3 className="text-lg font-semibold tracking-wide">
              Field 7: Judicial Officer Review & Escalation Portal
            </h3>
          </div>
          <span className="px-2.5 py-1 text-xs font-mono bg-slate-800 text-slate-400 rounded">
            Contract: {contractId.slice(0, 12)}...
          </span>
        </div>

        {escalationReason && (
          <div className="mb-4 p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg flex items-start gap-3 text-amber-200 text-sm">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block">Escalation Triggered:</span>
              {escalationReason}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50">
            <span className="text-slate-400 text-xs block">Calibrated Trust Score (T)</span>
            <span className="text-xl font-bold font-mono text-emerald-400">
              {(trustScore * 100).toFixed(1)}%
            </span>
          </div>
          <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50">
            <span className="text-slate-400 text-xs block">Conformal Risk Bound (σ)</span>
            <span className="text-xl font-bold font-mono text-cyan-400">
              {(riskScore * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-2">
              Judicial Adjudication Action
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setAction("APPROVED")}
                className={`py-2 px-3 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition ${
                  action === "APPROVED"
                    ? "bg-emerald-600/20 border-emerald-500 text-emerald-300"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600"
                }`}
              >
                <CheckCircle2 className="w-4 h-4" /> Approve
              </button>
              <button
                type="button"
                onClick={() => setAction("OVERRIDDEN")}
                className={`py-2 px-3 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition ${
                  action === "OVERRIDDEN"
                    ? "bg-amber-600/20 border-amber-500 text-amber-300"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600"
                }`}
              >
                <FileText className="w-4 h-4" /> Override
              </button>
              <button
                type="button"
                onClick={() => setAction("REJECTED")}
                className={`py-2 px-3 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition ${
                  action === "REJECTED"
                    ? "bg-rose-600/20 border-rose-500 text-rose-300"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600"
                }`}
              >
                <XCircle className="w-4 h-4" /> Reject
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Judicial Officer Override Notes & Statutory Rationale
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record statutory rationale for judicial override or escalation resolution under BSA 2023 §63(4)..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500/80"
              required
            />
          </div>

          {error && (
            <div className="text-xs text-rose-400 bg-rose-950/30 border border-rose-800 p-2.5 rounded-lg">
              {error}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 border-t border-slate-800 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 text-xs font-semibold rounded-lg shadow-md transition disabled:opacity-50 flex items-center gap-2"
            >
              <Lock className="w-3.5 h-3.5" /> Record Cryptographic Sign-Off
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
