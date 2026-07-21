"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth/auth-guard";
import { UploadZone } from "@/components/documents/upload-zone";
import { useCases } from "@/hooks/use-cases";
import { ArrowLeft, Scale, Plus, Trash2, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";
import type { PartyType } from "@/types/case";

export default function NewCasePage() {
  const router = useRouter();
  const { fileCase, isLoading, error } = useCases();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [caseType, setCaseType] = useState("Civil");
  const [priority, setPriority] = useState<"low" | "medium" | "high" | "critical">("medium");

  const [createdCaseId, setCreatedCaseId] = useState<string | null>(null);

  const [parties, setParties] = useState<Array<{ party_name: string; party_type: PartyType }>>([
    { party_name: "", party_type: "petitioner" },
    { party_name: "", party_type: "respondent" },
  ]);

  const addParty = () => {
    setParties([...parties, { party_name: "", party_type: "witness" }]);
  };

  const removeParty = (index: number) => {
    setParties(parties.filter((_, i) => i !== index));
  };

  const updateParty = (index: number, field: "party_name" | "party_type", value: string) => {
    const next = [...parties];
    next[index] = { ...next[index], [field]: value };
    setParties(next);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !caseType) return;

    const validParties = parties.filter((p) => p.party_name.trim().length > 0);

    try {
      const caseObj = await fileCase({
        title,
        description,
        case_type: caseType,
        priority,
        parties: validParties,
      });

      setCreatedCaseId(caseObj.id);
    } catch {
      // Error handled by hook
    }
  };

  return (
    <AuthGuard allowedRoles={["citizen", "lawyer", "admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white py-10 px-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {/* Back Link */}
          <Link
            href="/citizen"
            className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Dashboard
          </Link>

          {!createdCaseId ? (
            /* Step 1: File Case Form */
            <div className="glass rounded-2xl p-8 border border-white/10 space-y-6 shadow-2xl">
              <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                  <Scale className="h-5 w-5" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">File New Legal Case</h1>
                  <p className="text-xs text-gray-400">Enter case details and parties involved</p>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 text-sm text-red-400">
                  <AlertCircle className="h-5 w-5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                {/* Title */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Case Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. A. K. Sharma vs Municipal Corporation"
                    className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 px-4 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                {/* Case Type & Priority */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                      Case Category *
                    </label>
                    <select
                      value={caseType}
                      onChange={(e) => setCaseType(e.target.value)}
                      className="w-full rounded-xl border border-white/10 bg-[#161622] py-2.5 px-4 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="Civil">Civil</option>
                      <option value="Criminal">Criminal</option>
                      <option value="Consumer">Consumer</option>
                      <option value="Constitutional">Constitutional</option>
                      <option value="Family">Family</option>
                      <option value="Cybercrime">Cybercrime</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                      Priority Level
                    </label>
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value as any)}
                      className="w-full rounded-xl border border-white/10 bg-[#161622] py-2.5 px-4 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical / Urgent</option>
                    </select>
                  </div>
                </div>

                {/* Description */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Case Description / Summary
                  </label>
                  <textarea
                    rows={4}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Provide background context, facts, and legal relief sought..."
                    className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 px-4 text-sm text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                {/* Parties Involved */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                      Parties Involved
                    </label>
                    <button
                      type="button"
                      onClick={addParty}
                      className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:underline"
                    >
                      <Plus className="h-3.5 w-3.5" /> Add Party
                    </button>
                  </div>

                  {parties.map((p, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <input
                        type="text"
                        placeholder="Party Name"
                        value={p.party_name}
                        onChange={(e) => updateParty(idx, "party_name", e.target.value)}
                        className="flex-1 rounded-xl border border-white/10 bg-white/5 py-2 px-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                      />
                      <select
                        value={p.party_type}
                        onChange={(e) => updateParty(idx, "party_type", e.target.value)}
                        className="rounded-xl border border-white/10 bg-[#161622] py-2 px-3 text-sm text-white focus:outline-none focus:border-indigo-500"
                      >
                        <option value="petitioner">Petitioner</option>
                        <option value="respondent">Respondent</option>
                        <option value="witness">Witness</option>
                        <option value="intervener">Intervener</option>
                      </select>

                      {parties.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeParty(idx)}
                          className="text-gray-500 hover:text-red-400 p-1"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:brightness-110 disabled:opacity-50 mt-4"
                >
                  {isLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    "Submit Case Filing"
                  )}
                </button>
              </form>
            </div>
          ) : (
            /* Step 2: Case Created Success & Upload Attachments */
            <div className="glass rounded-2xl p-8 border border-white/10 space-y-6 shadow-2xl animate-fade-in text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle className="h-8 w-8" />
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-1">Case Filed Successfully!</h2>
                <p className="text-sm text-gray-400">
                  You can now attach petitions, affidavits, or evidence documents to your filing.
                </p>
              </div>

              {/* Upload Zone Component */}
              <div className="text-left pt-2">
                <UploadZone caseId={createdCaseId} />
              </div>

              <div className="pt-4 flex justify-center gap-4">
                <button
                  onClick={() => router.push("/citizen")}
                  className="rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg hover:brightness-110 transition-all"
                >
                  Go to Dashboard
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
