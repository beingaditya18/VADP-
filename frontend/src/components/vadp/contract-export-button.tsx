"use client";

import React from "react";
import type { VerificationContract } from "@/types/vadp";
import { Download, FileJson } from "lucide-react";

interface ContractExportButtonProps {
  contract: VerificationContract;
}

export const ContractExportButton: React.FC<ContractExportButtonProps> = ({ contract }) => {
  const handleExport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(contract, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `vadp-contract-${contract.id.substring(0, 8)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <button
      onClick={handleExport}
      className="inline-flex items-center px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors shadow-sm"
    >
      <FileJson className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
      Export JSON Contract
      <Download className="w-3 h-3 ml-1.5 text-slate-400" />
    </button>
  );
};
