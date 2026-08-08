"use client";

import Link from "next/link";
import { Scale, Home, Shield, BookOpen, Search, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-600/20 rounded-full blur-[128px] pointer-events-none" />

      <div className="max-w-md w-full glass p-8 rounded-3xl border border-white/10 text-center space-y-6 shadow-2xl relative z-10">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shadow-inner">
          <Scale className="h-8 w-8" />
        </div>

        <div className="space-y-2">
          <span className="font-mono text-xs uppercase font-bold text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
            Error 404
          </span>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Page Not Found</h1>
          <p className="text-xs text-gray-400 leading-relaxed">
            The requested legal docket path or system page does not exist or has been relocated within the VADP framework.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-left pt-2">
          <Link
            href="/"
            className="flex items-center gap-2 p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all group"
          >
            <Home className="h-4 w-4 text-indigo-400 group-hover:scale-110 transition-transform" />
            <div>
              <p className="text-xs font-bold text-white">Home Portal</p>
              <p className="text-[10px] text-gray-400">Landing Page</p>
            </div>
          </Link>

          <Link
            href="/citizen"
            className="flex items-center gap-2 p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all group"
          >
            <Shield className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
            <div>
              <p className="text-xs font-bold text-white">Citizen Portal</p>
              <p className="text-[10px] text-gray-400">Case Filings</p>
            </div>
          </Link>

          <Link
            href="/judge"
            className="flex items-center gap-2 p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all group"
          >
            <Scale className="h-4 w-4 text-purple-400 group-hover:scale-110 transition-transform" />
            <div>
              <p className="text-xs font-bold text-white">Judge Portal</p>
              <p className="text-[10px] text-gray-400">Bench Docket</p>
            </div>
          </Link>

          <Link
            href="/search"
            className="flex items-center gap-2 p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all group"
          >
            <Search className="h-4 w-4 text-emerald-400 group-hover:scale-110 transition-transform" />
            <div>
              <p className="text-xs font-bold text-white">Hybrid Search</p>
              <p className="text-[10px] text-gray-400">Vector Search</p>
            </div>
          </Link>
        </div>

        <div className="pt-2">
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-lg transition-all"
          >
            <ArrowLeft className="h-4 w-4" /> Return to Main Landing Page
          </Link>
        </div>
      </div>
    </div>
  );
}
