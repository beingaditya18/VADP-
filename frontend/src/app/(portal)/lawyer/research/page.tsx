"use client";

import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { RAGChat } from "@/components/rag/rag-chat";
import { useAuth } from "@/hooks/use-auth";
import { Scale, BookOpen, LogOut, ArrowLeft } from "lucide-react";

export default function LawyerResearchPage() {
  const { user, logout } = useAuth();

  return (
    <AuthGuard allowedRoles={["lawyer", "judge", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Navigation Bar */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Scale className="h-5 w-5" />
              </Link>
              <span className="font-bold tracking-tight text-lg text-white">Legal Research Portal</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400">
                Logged in as <strong className="text-white">{user?.full_name}</strong> ({user?.role})
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
        <main className="mx-auto max-w-7xl px-6 py-10 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">AI Legal Research & Precedent Analysis</h1>
              <p className="text-xs text-gray-400">
                FAISS semantic vector retrieval grounded with verifiable document citations.
              </p>
            </div>
          </div>

          {/* RAG Chat Assistant */}
          <RAGChat />
        </main>
      </div>
    </AuthGuard>
  );
}
