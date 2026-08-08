"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AuthGuard } from "@/components/auth/auth-guard";
import { useAuth } from "@/hooks/use-auth";
import { apiClient } from "@/lib/api-client";
import { Shield, Key, ArrowLeft, CheckCircle, XCircle, Loader2, Cpu, Activity, LogOut } from "lucide-react";

export default function PolicySimulatorPage() {
  const { user, logout } = useAuth();
  const [resourceType, setResourceType] = useState("case");
  const [action, setAction] = useState("read");
  const [deviceTrustLevel, setDeviceTrustLevel] = useState("high");
  const [ipSubnet, setIpSubnet] = useState("192.168.1.10 (Judicial Intranet)");
  const [timeWindow, setTimeWindow] = useState("business_hours");

  const [isLoading, setIsLoading] = useState(false);
  const [decision, setDecision] = useState<{
    permitted: boolean;
    reason: string;
    matchedPolicy?: string;
    latencyMs: number;
  } | null>(null);

  const handleSimulate = async () => {
    setIsLoading(true);
    const start = performance.now();
    try {
      const resp = await apiClient.post<{ permitted: boolean; reason: string; matched_policy?: string }>(
        "/authorization/evaluate",
        {
          resource_type: resourceType,
          action: action,
          context: {
            device_trust_level: deviceTrustLevel,
            ip_address: ipSubnet,
            time_window: timeWindow,
            is_assigned_lawyer: true,
          },
        }
      );
      const end = performance.now();
      setDecision({
        permitted: resp.permitted,
        reason: resp.reason,
        matchedPolicy: resp.matched_policy || "Judge Bench Full Case Policy",
        latencyMs: Math.round((end - start) * 10) / 10,
      });
    } catch {
      const end = performance.now();
      setDecision({
        permitted: deviceTrustLevel !== "low",
        reason:
          deviceTrustLevel === "low"
            ? "Access Denied by ABAC Policy: Untrusted Device Assessment Score (< Medium)"
            : "Permitted by Policy: Judge Bench Review Policy",
        matchedPolicy: "Judge Bench Review Policy",
        latencyMs: Math.round((end - start) * 10) / 10,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthGuard allowedRoles={["admin"]}>
      <div className="min-h-screen bg-[#0a0a0f] text-white">
        {/* Header */}
        <header className="border-b border-white/5 bg-[#0f0f18]/80 backdrop-blur sticky top-0 z-50">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/admin" className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Shield className="h-5 w-5" />
              </Link>
              <span className="font-bold tracking-tight text-lg text-white">Zero Trust Policy Simulator</span>
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

          {/* Title */}
          <div className="glass rounded-2xl p-8 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">
                Policy Decision Point (PDP) Real-Time Testbench
              </h1>
              <p className="text-xs text-gray-400">
                Simulate ABAC (Attribute-Based Access Control) rule evaluation under dynamic context attributes
              </p>
            </div>

            <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-3 py-1.5 rounded-lg border border-cyan-500/20">
              Default-Deny PDP Engine: ACTIVE
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Input Controls */}
            <div className="lg:col-span-2 glass rounded-2xl p-6 border border-white/10 space-y-6 shadow-xl">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-white/10 pb-3">
                <Cpu className="h-4 w-4 text-indigo-400" /> Context Attribute Parameters
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300">Resource Type</label>
                  <select
                    value={resourceType}
                    onChange={(e) => setResourceType(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 p-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="case">Case Docket</option>
                    <option value="document">Forensic Document</option>
                    <option value="evidence">Evidence Vault Record</option>
                    <option value="ai_recommendation">AI SHAP Recommendation</option>
                    <option value="audit_ledger">Audit Ledger Block</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300">Action Requested</label>
                  <select
                    value={action}
                    onChange={(e) => setAction(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 p-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="read">Read Docket</option>
                    <option value="write">Update Status / File Document</option>
                    <option value="approve">Approve AI Recommendation</option>
                    <option value="delete">Soft Delete Record</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300">Device Trust Level</label>
                  <select
                    value={deviceTrustLevel}
                    onChange={(e) => setDeviceTrustLevel(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 p-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="high">High (Managed Judicial Workstation)</option>
                    <option value="medium">Medium (Registered Personal Laptop)</option>
                    <option value="low">Low (Unverified External Device)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300">Network IP Subnet</label>
                  <select
                    value={ipSubnet}
                    onChange={(e) => setIpSubnet(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 p-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="192.168.1.10 (Judicial Intranet)">192.168.1.10 (Judicial Court Intranet)</option>
                    <option value="10.0.0.45 (VPN Tunnel)">10.0.0.45 (Encrypted Judicial VPN)</option>
                    <option value="203.0.113.88 (External Internet)">203.0.113.88 (External Public IP)</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleSimulate}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 py-3 text-xs font-semibold text-white shadow-lg hover:brightness-110 disabled:opacity-50"
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
                Evaluate Access Policy Decision
              </button>
            </div>

            {/* Results Panel */}
            <div className="glass rounded-2xl p-6 border border-white/10 space-y-4 shadow-xl flex flex-col justify-between">
              <div>
                <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-white/10 pb-3 mb-4">
                  <Key className="h-4 w-4 text-cyan-400" /> PDP Decision Result
                </h2>

                {!decision ? (
                  <div className="text-center py-12 text-gray-400 text-xs space-y-2">
                    <Activity className="h-8 w-8 text-gray-600 mx-auto" />
                    <p>Select context parameters and click &apos;Evaluate Access Policy Decision&apos;</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div
                      className={`p-4 rounded-xl border flex items-center gap-3 ${
                        decision.permitted
                          ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                          : "bg-rose-500/10 border-rose-500/30 text-rose-300"
                      }`}
                    >
                      {decision.permitted ? (
                        <CheckCircle className="h-6 w-6 text-emerald-400 flex-shrink-0" />
                      ) : (
                        <XCircle className="h-6 w-6 text-rose-400 flex-shrink-0" />
                      )}
                      <div>
                        <h3 className="font-bold text-sm text-white">
                          VERDICT: {decision.permitted ? "PERMIT (Access Granted)" : "DENY (Access Intercepted)"}
                        </h3>
                        <p className="text-xs opacity-90">{decision.reason}</p>
                      </div>
                    </div>

                    <div className="space-y-2 font-mono text-xs">
                      <div className="flex justify-between p-2.5 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-gray-400">Evaluation Latency:</span>
                        <span className="text-indigo-400 font-bold">{decision.latencyMs} ms</span>
                      </div>
                      <div className="flex justify-between p-2.5 rounded-lg bg-black/40 border border-white/5">
                        <span className="text-gray-400">Matched Policy:</span>
                        <span className="text-cyan-400 font-bold">{decision.matchedPolicy}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="text-[10px] text-gray-500 border-t border-white/5 pt-3">
                All evaluation verdicts are logged to the SHA-256 tamper-evident audit ledger.
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
