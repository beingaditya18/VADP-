"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, Scale, FileText, Layers, ArrowRight, Loader2, ShieldCheck } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface SearchResult {
  category: "case" | "document" | "vector_chunk";
  title: string;
  description: string;
  relevance_score: number;
  metadata: Record<string, any>;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setHasSearched(true);
    try {
      const data = await apiClient.get<{ items: SearchResult[] }>(`/search?q=${encodeURIComponent(query)}`);
      setResults(data.items || []);
    } catch {
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Scale className="h-5 w-5" />
            </div>
            <span className="font-bold tracking-tight text-lg text-white">Nyaya Hybrid Search</span>
          </Link>
        </div>
      </header>

      {/* Main Search */}
      <main className="mx-auto max-w-4xl px-6 py-12 space-y-8">
        <div className="text-center space-y-3">
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Universal Legal & Precedent Search
          </h1>
          <p className="text-sm text-gray-400 max-w-lg mx-auto">
            Combines full-text SQL matching with FAISS 384-dimensional vector semantic similarity.
          </p>
        </div>

        {/* Search Bar Input */}
        <form onSubmit={handleSearch} className="relative">
          <div className="flex items-center rounded-2xl glass border border-white/10 p-2 shadow-2xl focus-within:border-indigo-500/50">
            <Search className="h-5 w-5 text-gray-400 ml-4 flex-shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by case title, case number, document filename, or legal concept..."
              className="flex-1 bg-transparent border-0 py-3 px-4 text-sm text-white placeholder-gray-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 px-6 py-3 text-xs font-semibold text-white shadow-lg hover:brightness-110 disabled:opacity-50 transition-all flex items-center gap-2"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
            </button>
          </div>
        </form>

        {/* Results List */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
          </div>
        ) : hasSearched && results.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center text-gray-400 border border-white/5">
            No matching cases or precedent vectors found for "{query}".
          </div>
        ) : (
          <div className="space-y-4">
            {results.map((item, idx) => (
              <div key={idx} className="card card-glow p-6 space-y-2 border border-white/10 transition-all hover:border-indigo-500/40">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase font-bold px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-indigo-400">
                    {item.category.replace("_", " ")}
                  </span>
                  <span className="text-xs font-mono text-emerald-400 font-semibold">
                    Relevance: {Math.round(item.relevance_score * 100)}%
                  </span>
                </div>

                <h3 className="font-bold text-white text-base">{item.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed line-clamp-2">{item.description}</p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
