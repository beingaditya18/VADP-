"use client";

import React from "react";
import type { RAGProvenanceItem, RAGRetrievalMetadata } from "@/types/vadp";
import { BookOpen, Cpu, ExternalLink } from "lucide-react";

interface CitationVerificationPanelProps {
  citations: RAGProvenanceItem[];
  metadata?: RAGRetrievalMetadata;
}

export const CitationVerificationPanel: React.FC<CitationVerificationPanelProps> = ({
  citations,
  metadata,
}) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-semibold text-slate-100">RAG Citation Provenance</h3>
        </div>
        {metadata && (
          <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
            <span className="flex items-center">
              <Cpu className="w-3.5 h-3.5 mr-1 text-slate-500" />
              {metadata.embedding_model}
            </span>
            <span>Top-K: {metadata.top_k}</span>
            <span>Latency: {metadata.retrieval_latency_ms}ms</span>
          </div>
        )}
      </div>

      {(!citations || citations.length === 0) ? (
        <div className="p-4 text-center text-xs text-slate-400 border border-dashed border-slate-800 rounded-lg">
          No RAG citations bound to this contract. Legal advice generated from general jurisprudence principles.
        </div>
      ) : (
        <div className="space-y-3">
          {citations.map((item, idx) => (
            <div
              key={idx}
              className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400">
                  <span className="w-5 h-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-[10px]">
                    #{idx + 1}
                  </span>
                  <span className="font-mono text-slate-300">Chunk ID: {item.chunk_id || "N/A"}</span>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Score: {(item.similarity_score * 100).toFixed(1)}%
                </span>
              </div>

              <p className="text-xs text-slate-300 italic bg-slate-900/90 p-2.5 rounded border border-slate-800/60 mb-2 leading-relaxed">
                "{item.snippet}"
              </p>

              <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono pt-1">
                <span>Doc Reference: {item.document_id}</span>
                <a
                  href={`#doc-${item.document_id}`}
                  className="inline-flex items-center text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Inspect Source <ExternalLink className="w-3 h-3 ml-1" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
