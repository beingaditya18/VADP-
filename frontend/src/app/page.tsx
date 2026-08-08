import Link from "next/link";
import {
  Shield,
  Brain,
  FileSearch,
  Link as LinkIcon,
  Scale,
  Users,
  BarChart3,
  Lock,
  ArrowRight,
  ChevronRight,
  Sparkles,
  Eye,
  CheckCircle2,
  Cpu,
  FileCheck,
  Zap,
  Layers,
  Database,
  LockKeyhole,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#090a0f] text-white">
      {/* ── Background Grid & Dynamic Gradient Illumination ────────── */}
      <div className="fixed inset-0 hero-grid pointer-events-none opacity-40" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% -10%, rgba(99, 102, 241, 0.18) 0%, transparent 65%), radial-gradient(ellipse at 85% 60%, rgba(6, 182, 212, 0.08) 0%, transparent 45%), radial-gradient(ellipse at 15% 85%, rgba(16, 185, 129, 0.06) 0%, transparent 45%)",
        }}
      />

      {/* ── Header ────────────────────────────────────── */}
      <header className="relative z-10 border-b border-white/5 bg-[#0a0b12]/80 backdrop-blur-md sticky top-0">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-cyan-500 shadow-lg shadow-indigo-500/20">
              <Scale className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white">
                VADP
              </span>
              <span className="text-sm font-semibold tracking-wide text-indigo-400 ml-1.5 px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                PROVENANCE
              </span>
            </div>
          </div>

          <div className="hidden items-center gap-8 md:flex">
            <a
              href="#understanding-vadp"
              className="text-sm text-gray-300 transition-colors hover:text-white"
            >
              What is VADP?
            </a>
            <a
              href="#how-it-works"
              className="text-sm text-gray-300 transition-colors hover:text-white"
            >
              How It Works
            </a>
            <a
              href="#pillars"
              className="text-sm text-gray-300 transition-colors hover:text-white"
            >
              System Pillars
            </a>
            <a
              href="#portals"
              className="text-sm text-gray-300 transition-colors hover:text-white"
            >
              Judicial Portals
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:text-white"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:brightness-110"
            >
              Launch Portal
            </Link>
          </div>
        </nav>
      </header>

      {/* ── Hero Section ──────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-20 pt-16 md:pt-28">
        <div className="mx-auto max-w-4xl text-center">
          {/* Real VADP Badge */}
          <div className="animate-fade-in mb-8 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs sm:text-sm font-medium text-indigo-300 shadow-inner">
            <Sparkles className="h-4 w-4 text-cyan-400 animate-pulse" />
            <span>Verifiable AI Decision Provenance — Zero-Trust Judicial Decision Support</span>
          </div>

          {/* Headline */}
          <h1 className="animate-slide-up text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
            <span className="text-white">Tamper-Proof AI Assistance for </span>
            <br />
            <span className="bg-gradient-to-r from-indigo-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
              Modern Courtrooms
            </span>
          </h1>

          {/* Easy Language Subtitle */}
          <p className="animate-slide-up delay-200 mx-auto mt-6 max-w-3xl text-base leading-relaxed text-gray-300 opacity-90 sm:text-lg md:text-xl">
            When Artificial Intelligence recommends precedents to a Judge, how can courtrooms guarantee the AI didn't hallucinate or leak confidential records? <strong className="text-white">VADP solves this.</strong> It seals every AI suggestion inside a mathematical, cryptographically signed <strong>Verification Contract</strong> on an unalterable audit ledger.
          </p>

          {/* CTA Buttons */}
          <div className="animate-slide-up delay-300 mt-10 flex flex-col items-center justify-center gap-4 opacity-100 sm:flex-row">
            <Link
              href="/register"
              className="group flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-600 px-8 py-4 text-base font-semibold text-white shadow-xl shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:scale-[1.02] hover:brightness-110"
            >
              Explore Judicial Portal
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </Link>
            <a
              href="#understanding-vadp"
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-8 py-4 text-base font-medium text-gray-200 backdrop-blur transition-all hover:border-white/20 hover:bg-white/10 hover:text-white"
            >
              How VADP Protects Courts
              <ChevronRight className="h-4 w-4" />
            </a>
          </div>

          {/* Real Corpus Statistics */}
          <div className="animate-slide-up delay-400 mx-auto mt-16 grid max-w-4xl grid-cols-2 gap-4 rounded-2xl border border-white/10 bg-[#0e101a]/70 p-6 backdrop-blur sm:grid-cols-4 md:gap-8">
            {[
              { label: "Real Supreme Court Judgments", value: "1,500", desc: "ILDC Authentic Corpus" },
              { label: "Indexed Legal Chunks", value: "13,129", desc: "Vector & BM25 Embeddings" },
              { label: "Zero-Knowledge Proving", value: "250 ms", desc: "Groth16 192-Byte Proofs" },
              { label: "Verification Pass Rate", value: "100%", desc: "115/115 Automated Tests" },
            ].map((stat) => (
              <div key={stat.label} className="text-center p-3">
                <div className="text-2xl font-extrabold text-white sm:text-3xl md:text-4xl bg-gradient-to-br from-white to-gray-300 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="mt-1 text-xs font-semibold text-indigo-300">
                  {stat.label}
                </div>
                <div className="mt-0.5 text-[11px] text-gray-400">
                  {stat.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── What is Real VADP? (Easy Language Explanation) ───── */}
      <section id="understanding-vadp" className="relative z-10 border-t border-white/5 bg-[#0c0d16] py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">
              Plain English Guide
            </span>
            <h2 className="mt-2 text-3xl font-bold text-white md:text-4xl lg:text-5xl">
              What is Real <span className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">VADP</span> and Why Does it Matter?
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-base text-gray-300">
              Traditional AI models act like black boxes. In legal decision-making, an unverified AI suggestion can lead to bias, hallucinated precedents, or unauthorized data leaks. VADP transforms AI from a black box into a transparent, mathematically verifiable assistant.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            <div className="glass rounded-2xl p-8 border border-indigo-500/20 bg-gradient-to-b from-indigo-950/20 to-transparent relative overflow-hidden">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400 mb-6">
                <LockKeyhole className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">1. Zero-Trust Access Control</h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                Before AI reads a single confidential court file, VADP enforces strict <strong>Attribute-Based Access Control (ABAC)</strong>. A Lawyer only sees authorized evidence, a Citizen only accesses public dockets, and a Judge retains complete bench authority.
              </p>
            </div>

            <div className="glass rounded-2xl p-8 border border-cyan-500/20 bg-gradient-to-b from-cyan-950/20 to-transparent relative overflow-hidden">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 mb-6">
                <Brain className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">2. Authentic Precedent RAG</h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                Instead of inventing fake laws, VADP searches <strong>1,500 authentic Supreme Court of India judgments</strong> (13,129 vector chunks) and held-out SCOTUS/ECtHR corpora. Every citation is linked directly to authoritative precedent.
              </p>
            </div>

            <div className="glass rounded-2xl p-8 border border-emerald-500/20 bg-gradient-to-b from-emerald-950/20 to-transparent relative overflow-hidden">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 mb-6">
                <FileCheck className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">3. Verification Contracts</h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                Every AI output generates a digital <strong>Verification Contract</strong> (C_VADP). It binds together the exact prompt, document hashes, SHAP explainability feature scores, confidence rating, and cryptographic signatures.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Interactive How VADP Works Workflow ─────────────── */}
      <section id="how-it-works" className="relative z-10 py-24 bg-[#090a0f]">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <span className="text-xs font-bold uppercase tracking-widest text-cyan-400">
              End-to-End Decision Lifecycle
            </span>
            <h2 className="mt-2 text-3xl font-bold text-white md:text-4xl">
              How VADP Works in <span className="bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">4 Simple Steps</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-400">
              From initial query to final judicial sign-off, every step is mathematically recorded and verifiably complete.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                step: "01",
                title: "Security Clearance",
                desc: "User token and role attributes are checked. Policy engine evaluates environment, jurisdiction, and security clearance.",
                icon: Shield,
                badge: "Zero-Trust ABAC",
              },
              {
                step: "02",
                title: "Legal Precedent Retrieval",
                desc: "RAG engine searches 1,500 Supreme Court of India rulings (13,129 chunks). Retrieves authoritative legal citations.",
                icon: Database,
                badge: "1,500 ILDC Corpus",
              },
              {
                step: "03",
                title: "SHAP Explainability",
                desc: "Calculates feature importance weights (p_abac, theta_rag, psi_shap) and assigns an audited Trust Score (T_trust).",
                icon: Cpu,
                badge: "SHAP Transparency",
              },
              {
                step: "04",
                title: "Merkle Audit Ledger",
                desc: "Signs contract with ECDSA/Ed25519, computes Merkle root, and generates Groth16 Zero-Knowledge Inclusion Proof.",
                icon: LinkIcon,
                badge: "Groth16 ZKP Proof",
              },
            ].map((s) => (
              <div key={s.step} className="card relative p-6 border border-white/10 bg-[#0e101a] hover:border-indigo-500/40 transition-all group">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-3xl font-black text-indigo-500/40 group-hover:text-indigo-400 transition-colors font-mono">
                    {s.step}
                  </span>
                  <span className="text-[11px] font-medium text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-full">
                    {s.badge}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                  <s.icon className="h-4 w-4 text-cyan-400" />
                  {s.title}
                </h3>
                <p className="text-xs leading-relaxed text-gray-400">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Five Pillars Section ──────────────────────────── */}
      <section id="pillars" className="relative z-10 border-y border-white/5 bg-[#0c0d16] py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">
              Five Core Pillars of
              <span className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent"> VADP System Architecture</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-400">
              Built on production-grade zero-trust principles, cryptographic ledgers, and explainable legal intelligence.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: Shield,
                title: "Zero Trust ABAC Security",
                description:
                  "Continuous verification on every request. RBAC + ABAC policy engine with Z3 formal verifier. Never trust, always verify.",
                gradient: "from-indigo-500 to-purple-500",
              },
              {
                icon: Brain,
                title: "SHAP Explainable AI",
                description:
                  "SHAP-based feature importance. Natural language explanations. Trust & confidence scoring with full transparency.",
                gradient: "from-cyan-500 to-blue-500",
              },
              {
                icon: FileSearch,
                title: "1,500-Case Legal RAG",
                description:
                  "Dense & sparse retrieval over 1,500 Supreme Court judgments (13,129 vector chunks). Precision citation verification.",
                gradient: "from-emerald-500 to-teal-500",
              },
              {
                icon: LinkIcon,
                title: "VADP Audit Ledger",
                description:
                  "Verification Contracts signed with ECDSA, hash-chained in Decision Provenance Timelines and Merkle trees.",
                gradient: "from-amber-500 to-orange-500",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="card group relative overflow-hidden p-6 border border-white/10 bg-[#0e101a] hover:border-white/20 transition-all"
              >
                <div
                  className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feature.gradient} shadow-lg`}
                >
                  <feature.icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="mb-2 text-lg font-bold text-white">
                  {feature.title}
                </h3>
                <p className="text-xs leading-relaxed text-gray-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Role Portals Section ──────────────────────── */}
      <section id="portals" className="relative z-10 py-24 bg-[#090a0f]">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">
              Tailored Portals for Every
              <span className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent"> Judicial Stakeholder</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-400">
              Each user role gets a dedicated interface engineered for their exact workflow and permission tier.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                role: "Judge Master Bench",
                icon: Scale,
                description:
                  "Review bench dockets, examine RAG citations from 1,500 ILDC Supreme Court judgments, inspect SHAP explainability, and approve decision contracts.",
                features: ["AI Bench Support", "SHAP Attributions", "1,500 ILDC Corpus"],
                link: "/login",
                color: "cyan",
              },
              {
                role: "Lawyer Counsel",
                icon: FileSearch,
                description:
                  "Conduct AI-powered legal research across 1,500 Supreme Court rulings, prepare arguments, and review precedent relevance scores.",
                features: ["Legal RAG Research", "Citation Verification", "Document Prep"],
                link: "/login",
                color: "purple",
              },
              {
                role: "Citizen Litigant",
                icon: Users,
                description:
                  "File cases, securely upload evidence, track hearing timelines, and view public decision provenance receipts.",
                features: ["Case Filing", "Evidence Vault", "Status Tracking"],
                link: "/login",
                color: "blue",
              },
              {
                role: "System Administrator",
                icon: Shield,
                description:
                  "Configure ABAC policies, monitor Zero Trust access attempts, inspect Merkle audit logs, and manage user roles.",
                features: ["Policy Simulator", "Audit Ledger", "System Analytics"],
                link: "/login",
                color: "amber",
              },
            ].map((portal) => (
              <div
                key={portal.role}
                className="card group p-6 border border-white/10 bg-[#0e101a] hover:border-indigo-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                    <portal.icon className="h-6 w-6" />
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-white">
                    {portal.role}
                  </h3>
                  <p className="mb-4 text-xs text-gray-400 leading-relaxed">
                    {portal.description}
                  </p>
                  <div className="flex flex-wrap gap-1.5 mb-6">
                    {portal.features.map((f) => (
                      <span
                        key={f}
                        className="rounded-full bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-0.5 text-[11px] text-indigo-300 font-medium"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>

                <Link
                  href={portal.link}
                  className="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 py-2.5 text-xs font-semibold text-gray-300 hover:border-indigo-500/40 hover:bg-indigo-600 hover:text-white transition-all"
                >
                  Access Portal <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="relative z-10 border-t border-white/5 bg-[#07080d] py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2">
              <Scale className="h-5 w-5 text-indigo-400" />
              <span className="text-base font-bold text-white">VADP</span>
              <span className="text-xs text-gray-400">
                — Verifiable AI Decision Provenance Platform
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Empowering courtrooms with transparent, tamper-proof, and explainable AI decision support.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
