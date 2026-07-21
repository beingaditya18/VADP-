"use client";

import { useState } from "react";
import { FileText, ChevronRight, X } from "lucide-react";
import type { Citation } from "@/types/ai";

interface CitationBadgeProps {
  citation: Citation;
  index: number;
}

export function CitationBadge({ citation, index }: CitationBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="inline-block relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500/10 px-2.5 py-1 text-xs font-mono text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors"
      >
        <FileText className="h-3 w-3" />
        Source #{index + 1}: {citation.file_name} ({Math.round(citation.relevance_score * 100)}%)
      </button>

      {/* Popover excerpt modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="glass max-w-lg w-full rounded-2xl p-6 border border-white/10 space-y-4 shadow-2xl relative">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" />
                <h4 className="font-bold text-white text-sm">{citation.file_name}</h4>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between text-gray-400 font-mono">
                <span>Chunk #{citation.chunk_index}</span>
                <span className="text-emerald-400">Relevance: {(citation.relevance_score * 100).toFixed(1)}%</span>
              </div>
              <div className="rounded-xl bg-black/40 p-4 font-mono text-gray-300 border border-white/5 whitespace-pre-wrap leading-relaxed">
                {citation.excerpt}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
