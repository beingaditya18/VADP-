"use client";

import Link from "next/link";
import { Calendar, FileText, ArrowRight, ShieldCheck } from "lucide-react";
import { formatDate, getStatusColor } from "@/lib/utils";
import type { Case } from "@/types/case";

interface CaseCardProps {
  caseObj: Case;
  hrefPrefix?: string;
}

export function CaseCard({ caseObj, hrefPrefix = "/citizen/cases" }: CaseCardProps) {
  const statusBadgeColor = getStatusColor(caseObj.status);

  return (
    <div className="card card-glow group relative overflow-hidden p-6 transition-all border border-white/10 hover:border-indigo-500/40">
      {/* Top row: Case Number & Status Badge */}
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className="font-mono text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20">
          {caseObj.case_number}
        </span>
        <span className={`text-xs font-semibold capitalize px-2.5 py-1 rounded-full border ${statusBadgeColor}`}>
          {caseObj.status.replace("_", " ")}
        </span>
      </div>

      {/* Case Title */}
      <h3 className="text-lg font-semibold text-white group-hover:text-indigo-300 transition-colors line-clamp-1 mb-2">
        {caseObj.title}
      </h3>

      {/* Description */}
      {caseObj.description && (
        <p className="text-sm text-gray-400 line-clamp-2 mb-4 leading-relaxed">
          {caseObj.description}
        </p>
      )}

      {/* Footer Info */}
      <div className="flex items-center justify-between border-t border-white/5 pt-4 text-xs text-gray-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-gray-500" />
            {caseObj.case_type}
          </span>
          <span className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-gray-500" />
            Filed: {formatDate(caseObj.filing_date)}
          </span>
        </div>

        <Link
          href={`${hrefPrefix}/${caseObj.id}`}
          className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          View Case
          <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </div>
  );
}
