"use client";

import Link from "next/link";
import { Calendar, FileText, ArrowRight, ShieldCheck, Scale, Award } from "lucide-react";
import { formatDate, getStatusColor } from "@/lib/utils";
import type { Case } from "@/types/case";

interface CaseCardProps {
  caseObj: Case;
  hrefPrefix?: string;
}

export function CaseCard({ caseObj, hrefPrefix = "/judge/cases" }: CaseCardProps) {
  const statusBadgeColor = getStatusColor(caseObj.status);
  
  // Extract citation & trust score from metadata_ if available
  const citation = (caseObj as any).metadata_?.citation || "INSC 2016";
  const trustScore = (caseObj as any).metadata_?.trust_score || 0.92;
  const courtName = "Supreme Court of India";

  return (
    <div className="card card-glow group relative overflow-hidden p-6 transition-all border border-white/10 hover:border-indigo-500/50 bg-[#12121e]/90 rounded-2xl flex flex-col justify-between shadow-xl">
      <div>
        {/* Top row: Case Number & Status Badge */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20">
            {caseObj.case_number}
          </span>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
              <ShieldCheck className="h-3 w-3" />
              {Math.round((trustScore > 1 ? trustScore / 100 : trustScore) * 100)}% Trust
            </span>
            <span className={`text-xs font-semibold capitalize px-2.5 py-1 rounded-full border ${statusBadgeColor}`}>
              {caseObj.status.replace("_", " ")}
            </span>
          </div>
        </div>

        {/* Case Title */}
        <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors line-clamp-2 mb-2 leading-snug">
          {caseObj.title}
        </h3>

        {/* Description / Summary */}
        {caseObj.description && (
          <p className="text-xs text-gray-400 line-clamp-2 mb-4 leading-relaxed">
            {caseObj.description}
          </p>
        )}
      </div>

      <div>
        {/* Court & Citation Info */}
        <div className="flex items-center justify-between text-[11px] text-gray-400 mb-4 bg-white/5 p-2 rounded-lg">
          <span className="flex items-center gap-1.5 font-medium text-gray-300">
            <Scale className="h-3.5 w-3.5 text-indigo-400" />
            {courtName}
          </span>
          <span className="font-mono text-gray-400">{citation}</span>
        </div>

        {/* Footer Info */}
        <div className="flex items-center justify-between border-t border-white/5 pt-3 text-xs text-gray-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 text-[11px]">
              <FileText className="h-3 w-3 text-indigo-400" />
              {caseObj.case_type}
            </span>
            <span className="flex items-center gap-1 text-[11px]">
              <Calendar className="h-3 w-3 text-gray-500" />
              {formatDate(caseObj.filing_date)}
            </span>
          </div>

          <Link
            href={`${hrefPrefix}/${caseObj.id}`}
            className="flex items-center gap-1 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors bg-indigo-500/10 hover:bg-indigo-500/20 px-3 py-1.5 rounded-lg border border-indigo-500/30"
          >
            View Case
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </div>
  );
}
