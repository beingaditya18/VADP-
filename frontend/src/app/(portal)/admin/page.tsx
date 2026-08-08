"use client";

import { useState } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { useAuth } from "@/hooks/use-auth";
import { PdfVerificationModal } from "@/components/evidence/PdfVerificationModal";
import { AiModelControlPanel } from "@/components/ai/ai-model-control-panel";
import { Shield, Layers, Users, Key, Activity, LogOut, ArrowRight, Cpu, FileCheck } from "lucide-react";

export default function AdminControlCenterPage() {
  const { user, logout } = useAuth();
  const [isPdfModalOpen, setIsPdfModalOpen] = useState(false);

  return (
    <AuthGuard allowedRoles={["admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Header */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Shield className="h-5 w-5" />
              </div>
              <span className="font-bold tracking-tight text-lg text-white">System Admin Control Center</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400">
                Administrator <strong className="text-white">{user?.full_name}</strong>
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

        {/* Main */}
        <main className="mx-auto max-w-7xl px-6 py-10 space-y-8">
          <div className="glass rounded-2xl p-8 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">VADP Security & Infrastructure Management</h1>
              <p className="text-sm text-gray-400">
                Manage ABAC access policies, verify tamper-evident audit ledger, and monitor system health.
              </p>
            </div>

            <button
              onClick={() => setIsPdfModalOpen(true)}
              className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold rounded-xl shadow-xl shadow-indigo-500/20 transition-all"
            >
              <FileCheck className="h-4 w-4" />
              <span>Launch PDF Forensic Tamper Lab</span>
            </button>
          </div>

          {/* AI Decision Model Control Panel */}
          <AiModelControlPanel />

          {/* Quick Action Navigation Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Link
              href="/admin/audit"
              className="card card-glow p-6 space-y-4 border border-white/10 hover:border-indigo-500/40 group transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Layers className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-white group-hover:text-indigo-300 transition-colors flex items-center justify-between">
                  Audit Block Explorer
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </h3>
                <p className="text-xs text-gray-400">SHA-256 hash chain, Merkle root verification & ECDSA signatures</p>
              </div>
            </Link>

            <Link
              href="/admin/policy-simulator"
              className="card card-glow p-6 space-y-4 border border-white/10 hover:border-indigo-500/40 group transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <Cpu className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-white group-hover:text-rose-300 transition-colors flex items-center justify-between">
                  ABAC PDP Testbench
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </h3>
                <p className="text-xs text-gray-400">Real-time Zero Trust attribute rule evaluation & verdict latency</p>
              </div>
            </Link>

            <Link
              href="/admin/verification"
              className="card card-glow p-6 space-y-4 border border-white/10 hover:border-indigo-500/40 group transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Shield className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-white group-hover:text-purple-300 transition-colors flex items-center justify-between">
                  VADP Contract Explorer
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </h3>
                <p className="text-xs text-gray-400">Verifiable AI Decision Provenance cryptographic contract inspector</p>
              </div>
            </Link>

            <Link
              href="/search"
              className="card card-glow p-6 space-y-4 border border-white/10 hover:border-indigo-500/40 group transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Activity className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-white group-hover:text-cyan-300 transition-colors flex items-center justify-between">
                  Universal Hybrid Search
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </h3>
                <p className="text-xs text-gray-400">Full-text SQL + FAISS 384-dimensional vector similarity index</p>
              </div>
            </Link>

            <Link
              href="/lawyer/research"
              className="card card-glow p-6 space-y-4 border border-white/10 hover:border-indigo-500/40 group transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Key className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-white group-hover:text-emerald-300 transition-colors flex items-center justify-between">
                  AI Precedent Engine
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </h3>
                <p className="text-xs text-gray-400">RAG legal research assistant with prompt injection shield</p>
              </div>
            </Link>
          </div>
        </main>

        <PdfVerificationModal
          isOpen={isPdfModalOpen}
          onClose={() => setIsPdfModalOpen(false)}
        />
      </div>
    </AuthGuard>
  );
}

