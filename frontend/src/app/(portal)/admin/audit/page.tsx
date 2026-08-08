"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { BlockCard } from "@/components/ledger/block-card";
import { ChainStatusBanner } from "@/components/ledger/chain-status-banner";
import { MerkleTreeVisualizer } from "@/components/ledger/merkle-tree-visualizer";
import { useLedger } from "@/hooks/use-ledger";
import { useAuth } from "@/hooks/use-auth";
import { Shield, Layers, Plus, ArrowLeft, Loader2, LogOut } from "lucide-react";

export default function AdminAuditPage() {
  const { user, logout } = useAuth();
  const { blocks, verificationResult, isLoading, fetchBlocks, verifyChain, sealBlock } = useLedger();

  useEffect(() => {
    fetchBlocks();
    verifyChain();
  }, [fetchBlocks, verifyChain]);

  return (
    <AuthGuard allowedRoles={["admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Navigation Bar */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/admin" className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Shield className="h-5 w-5" />
              </Link>
              <span className="font-bold tracking-tight text-lg text-white">Admin Audit Ledger Explorer</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400">
                Logged in as <strong className="text-white">{user?.full_name}</strong>
              </span>
              <button
                onClick={logout}
                className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" /> Sign Out
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="mx-auto max-w-7xl px-6 py-10 space-y-8">
          <Link href="/admin" className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="h-4 w-4" /> Back to Admin Control Center
          </Link>

          {/* Header row */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">Tamper-Evident Audit Ledger</h1>
              <p className="text-xs text-gray-400">
                SHA-256 hash chaining, Merkle tree roots, and ECDSA P-256 digital signatures
              </p>
            </div>

            <button
              onClick={() => sealBlock()}
              disabled={isLoading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg hover:brightness-110 disabled:opacity-50"
            >
              <Plus className="h-4 w-4" /> Seal Pending Block
            </button>
          </div>

          {/* Chain Verification Status Banner */}
          <ChainStatusBanner
            result={verificationResult}
            onVerify={() => verifyChain()}
            isVerifying={isLoading}
          />

          {/* Merkle Tree Inclusion Proof Inspector */}
          <MerkleTreeVisualizer block={blocks[0]} />

          {/* Block List */}
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-400" />
              Block Chain ({blocks.length} Total Blocks)
            </h2>

            {isLoading && blocks.length === 0 ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
              </div>
            ) : blocks.length === 0 ? (
              <div className="glass rounded-2xl p-12 text-center text-gray-400 border border-white/5 space-y-3">
                <p className="text-sm">No ledger blocks sealed yet.</p>
                <button
                  onClick={() => sealBlock()}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:underline"
                >
                  <Plus className="h-3.5 w-3.5" /> Seal genesis block from current audit entries
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {blocks.map((block) => (
                  <BlockCard key={block.id} block={block} />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
