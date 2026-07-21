"use client";

import { useState } from "react";
import { Link2, ShieldCheck, Key, Layers, ChevronDown, ChevronUp, Clock, Hash } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { LedgerBlock } from "@/types/ledger";

interface BlockCardProps {
  block: LedgerBlock;
}

export function BlockCard({ block }: BlockCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="card card-glow border border-white/10 p-6 space-y-4 transition-all hover:border-indigo-500/40">
      {/* Top row: Block Index & Signature badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-mono font-bold text-sm">
            #{block.block_index}
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Block #{block.block_index}</h3>
            <span className="text-xs text-gray-400 flex items-center gap-1">
              <Clock className="h-3 w-3" /> {formatDate(block.timestamp)}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {block.signature ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
              <Key className="h-3.5 w-3.5" /> ECDSA Signed
            </span>
          ) : (
            <span className="text-xs text-gray-500">Unsigned</span>
          )}
          <span className="rounded-md bg-white/5 px-2.5 py-1 text-xs font-mono text-gray-400 border border-white/5">
            {block.entries_count} Entries
          </span>
        </div>
      </div>

      {/* Hashes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
        {/* Block Hash */}
        <div className="rounded-xl bg-black/40 p-3 border border-white/5 space-y-1">
          <span className="text-gray-500 text-[10px] uppercase tracking-wider block">Block Hash (SHA-256)</span>
          <span className="text-cyan-400 truncate block">{block.block_hash}</span>
        </div>

        {/* Previous Hash */}
        <div className="rounded-xl bg-black/40 p-3 border border-white/5 space-y-1">
          <span className="text-gray-500 text-[10px] uppercase tracking-wider flex items-center gap-1">
            <Link2 className="h-3 w-3 text-indigo-400" /> Previous Hash
          </span>
          <span className="text-indigo-300 truncate block">{block.previous_hash}</span>
        </div>
      </div>

      {/* Merkle Root */}
      {block.merkle_root && (
        <div className="rounded-xl bg-indigo-950/20 p-3 border border-indigo-500/20 text-xs font-mono flex items-center justify-between gap-3">
          <span className="text-gray-400 flex items-center gap-1.5">
            <Layers className="h-4 w-4 text-indigo-400" /> Merkle Root:
          </span>
          <span className="text-indigo-300 truncate">{block.merkle_root}</span>
        </div>
      )}

      {/* Accordion toggle for audit entries */}
      {block.entries && block.entries.length > 0 && (
        <div className="pt-2 border-t border-white/5">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center justify-between w-full text-xs font-semibold text-gray-400 hover:text-white transition-colors"
          >
            <span>View {block.entries.length} Sealed Audit Entries</span>
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {isExpanded && (
            <div className="mt-3 space-y-2 animate-fade-in">
              {block.entries.map((entry) => (
                <div key={entry.id} className="rounded-lg bg-white/5 p-3 text-xs space-y-1 border border-white/5">
                  <div className="flex items-center justify-between text-gray-300 font-semibold">
                    <span className="capitalize text-indigo-400">{entry.entry_type.replace("_", " ")}</span>
                    <span className="text-[10px] font-mono text-gray-500">{entry.data_hash.substring(0, 16)}...</span>
                  </div>
                  <p className="text-gray-300">{entry.action}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
