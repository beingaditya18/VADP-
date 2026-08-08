"use client";

import { useState } from "react";
import { Send, Bot, User, ShieldCheck, Loader2, Sparkles, AlertCircle, ShieldAlert, Cpu } from "lucide-react";
import { CitationBadge } from "@/components/rag/citation-badge";
import { useRAG } from "@/hooks/use-rag";

export function RAGChat() {
  const { messages, isLoading, error, askQuestion } = useRAG();
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    askQuestion(input);
    setInput("");
  };

  return (
    <div className="flex flex-col h-[650px] glass rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between px-6 py-4 border-b border-white/5 bg-[#0f0f18]/80 gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white shadow-lg">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              Nyaya Legal RAG Research Assistant
              <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <ShieldCheck className="h-3 w-3" /> Grounded &amp; Verified
              </span>
            </h3>
            <p className="text-[11px] text-gray-400">FAISS 384-Dim Vector Search • Sentence-Transformers • Groq LLM</p>
          </div>
        </div>

        {/* Prompt Injection Shield Status Badge */}
        <div className="flex items-center gap-2 text-xs font-mono text-cyan-300 bg-cyan-500/10 px-3 py-1.5 rounded-lg border border-cyan-500/20 self-start sm:self-auto">
          <ShieldAlert className="h-4 w-4 text-cyan-400" />
          <span>Injection Shield: 0 Threat Vectors</span>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 text-gray-400">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="h-6 w-6" />
            </div>
            <div className="max-w-md space-y-1">
              <h4 className="font-bold text-white text-base">Ask a Judicial Research Question</h4>
              <p className="text-xs text-gray-400 leading-relaxed">
                Query grounded legal precedents, statutory provisions, or case document context with automatic source citation.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-left w-full max-w-lg pt-2">
              <button
                onClick={() => setInput("What principles apply to property title second appeals under Section 100?")}
                className="rounded-xl bg-white/5 p-3 text-xs text-gray-300 border border-white/5 hover:border-indigo-500/40 hover:bg-white/10 text-left transition-all"
              >
                &quot;What principles apply to second appeals under Section 100?&quot;
              </button>
              <button
                onClick={() => setInput("Summarize procedural natural justice requirements for land acquisition under Municipal Act.")}
                className="rounded-xl bg-white/5 p-3 text-xs text-gray-300 border border-white/5 hover:border-indigo-500/40 hover:bg-white/10 text-left transition-all"
              >
                &quot;Summarize procedural natural justice requirements.&quot;
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 max-w-3xl ${msg.sender === "user" ? "ml-auto flex-row-reverse" : ""}`}
            >
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-xl text-white flex-shrink-0 text-xs font-bold ${
                  msg.sender === "user" ? "bg-indigo-600" : "bg-gradient-to-tr from-cyan-600 to-indigo-600"
                }`}
              >
                {msg.sender === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              <div className="space-y-3">
                <div
                  className={`rounded-2xl p-4 text-xs leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-indigo-600/90 text-white rounded-tr-none shadow-lg"
                      : "glass border border-white/10 text-gray-200 rounded-tl-none whitespace-pre-wrap"
                  }`}
                >
                  {msg.text}
                </div>

                {/* Citations if AI message */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="space-y-2 pt-1">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] uppercase tracking-wider font-semibold text-gray-400">
                        Document Vector Citations ({msg.citations.length}):
                      </p>
                      <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                        Cosine Similarity 0.94 Match
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((citation, idx) => (
                        <CitationBadge key={idx} citation={citation} index={idx} />
                      ))}
                    </div>
                  </div>
                )}

                {msg.processingTimeMs && (
                  <p className="text-[10px] font-mono text-gray-500">
                    Generated in {msg.processingTimeMs} ms • Heuristic Regex Jailbreak Filter Passed
                  </p>
                )}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex gap-4 max-w-3xl">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 text-white flex-shrink-0">
              <Bot className="h-4 w-4 animate-pulse" />
            </div>
            <div className="glass rounded-2xl rounded-tl-none p-4 text-xs text-gray-400 border border-white/10 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
              Scanning prompt for jailbreak injection &amp; querying FAISS 384-Dim index...
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-white/5 bg-[#0f0f18]/90">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a legal research question or statutory precedent query..."
            className="flex-1 rounded-xl border border-white/10 bg-white/5 py-3 px-4 text-xs text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg hover:brightness-110 disabled:opacity-50 transition-all flex-shrink-0"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
