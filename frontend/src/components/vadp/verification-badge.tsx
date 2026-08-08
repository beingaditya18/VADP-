"use client";

import React from "react";
import type { VerificationContract } from "@/types/vadp";
import { CheckCircle, AlertTriangle, ShieldCheck, HelpCircle } from "lucide-react";

interface VerificationBadgeProps {
  contract?: VerificationContract | null;
  status?: string;
  size?: "sm" | "md" | "lg";
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({
  contract,
  status: inputStatus,
  size = "md",
}) => {
  const status = contract ? contract.completeness_status : inputStatus || "unknown";

  const getBadgeConfig = () => {
    switch (status) {
      case "complete":
        return {
          label: "VADP Verified",
          bgColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
          icon: <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" />,
        };
      case "awaiting_review":
      case "awaiting_review_and_ledger":
        return {
          label: "Awaiting Review",
          bgColor: "bg-amber-500/10 text-amber-400 border-amber-500/30",
          icon: <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-400" />,
        };
      case "awaiting_ledger":
        return {
          label: "Awaiting Ledger",
          bgColor: "bg-blue-500/10 text-blue-400 border-blue-500/30",
          icon: <CheckCircle className="w-3.5 h-3.5 mr-1 text-blue-400" />,
        };
      case "incomplete":
        return {
          label: "Incomplete Contract",
          bgColor: "bg-rose-500/10 text-rose-400 border-rose-500/30",
          icon: <AlertTriangle className="w-3.5 h-3.5 mr-1 text-rose-400" />,
        };
      default:
        return {
          label: "Unverified",
          bgColor: "bg-slate-500/10 text-slate-400 border-slate-500/30",
          icon: <HelpCircle className="w-3.5 h-3.5 mr-1 text-slate-400" />,
        };
    }
  };

  const config = getBadgeConfig();
  const sizeClasses =
    size === "sm"
      ? "text-xs px-2 py-0.5"
      : size === "lg"
      ? "text-sm px-3 py-1.5"
      : "text-xs px-2.5 py-1";

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${config.bgColor} ${sizeClasses}`}
    >
      {config.icon}
      {config.label}
    </span>
  );
};
