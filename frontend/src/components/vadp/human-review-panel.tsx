"use client";

import React, { useState } from "react";
import type { VerificationContract } from "@/types/vadp";
import { useVADP } from "@/hooks/use-vadp";
import { UserCheck, CheckCircle2, XCircle, AlertTriangle, ShieldAlert, Lock, MessageSquare } from "lucide-react";

interface HumanReviewPanelProps {
  contract: VerificationContract;
  onReviewSubmitted?: (updated: VerificationContract) => void;
}

export const HumanReviewPanel: React.FC<HumanReviewPanelProps> = ({
  contract,
  onReviewSubmitted,
}) => {
  const { reviewContract, finalizeContract, loading } = useVADP();
  const [notes, setNotes] = useState("");
  const [selectedAction, setSelectedAction] = useState<string | null>(null);

  const handleReview = async (action: string) => {
    setSelectedAction(action);
    const updated = await reviewContract(contract.id, action, notes);
    if (updated && onReviewSubmitted) {
      onReviewSubmitted(updated);
    }
  };

  const handleFinalize = async () => {
    const updated = await finalizeContract(contract.id);
    if (updated && onReviewSubmitted) {
      onReviewSubmitted(updated);
    }
  };

  const isPending = contract.human_review.status === "pending_review";

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <UserCheck className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-slate-100">Human Judicial Oversight</h3>
        </div>
        <span
          className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
            isPending
              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
          }`}
        >
          Status: {contract.human_review.status.replace("_", " ")}
        </span>
      </div>

      {!isPending && (
        <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg mb-4 text-xs space-y-2">
          <div className="flex items-center justify-between text-slate-300">
            <span className="font-semibold">Reviewer: {contract.human_review.reviewed_by || "Judge"}</span>
            <span className="text-slate-400 font-mono">
              {contract.human_review.reviewed_at
                ? new Date(contract.human_review.reviewed_at).toLocaleString()
                : "N/A"}
            </span>
          </div>
          <div className="text-slate-400">
            Action: <span className="font-semibold text-indigo-300 capitalize">{contract.human_review.action}</span>
          </div>
          {contract.human_review.notes && (
            <div className="text-slate-300 italic border-l-2 border-indigo-500 pl-2.5 mt-1">
              "{contract.human_review.notes}"
            </div>
          )}
        </div>
      )}

      {/* Review Actions Form */}
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center">
            <MessageSquare className="w-3.5 h-3.5 mr-1 text-slate-400" />
            Judicial Review Notes
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add judicial comments or reasoning for approval/rejection..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none h-20"
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button
            onClick={() => handleReview("approved")}
            disabled={loading}
            className="flex items-center justify-center px-3 py-2 bg-emerald-600/90 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
            Approve
          </button>
          <button
            onClick={() => handleReview("rejected")}
            disabled={loading}
            className="flex items-center justify-center px-3 py-2 bg-rose-600/90 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            <XCircle className="w-3.5 h-3.5 mr-1.5" />
            Reject
          </button>
          <button
            onClick={() => handleReview("flagged")}
            disabled={loading}
            className="flex items-center justify-center px-3 py-2 bg-amber-600/90 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
            Flag Case
          </button>
          <button
            onClick={() => handleReview("override")}
            disabled={loading}
            className="flex items-center justify-center px-3 py-2 bg-purple-600/90 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            <ShieldAlert className="w-3.5 h-3.5 mr-1.5" />
            Override
          </button>
        </div>

        {!contract.finalized_at && contract.completeness.overall_complete && (
          <div className="pt-3 border-t border-slate-800">
            <button
              onClick={handleFinalize}
              disabled={loading}
              className="w-full flex items-center justify-center px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-bold rounded-lg shadow-md transition-all disabled:opacity-50"
            >
              <Lock className="w-4 h-4 mr-2" />
              Finalize & Freeze Contract
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
