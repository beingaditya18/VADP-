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
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* ── Background Effects ────────────────────────── */}
      <div className="fixed inset-0 hero-grid pointer-events-none" />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% -20%, rgba(99, 102, 241, 0.12) 0%, transparent 60%), radial-gradient(ellipse at 80% 60%, rgba(6, 182, 212, 0.06) 0%, transparent 40%)",
        }}
      />

      {/* ── Header ────────────────────────────────────── */}
      <header className="relative z-10 border-b border-white/5">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500">
              <Scale className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white">
                Nyaya
              </span>
              <span className="text-lg font-light tracking-tight text-indigo-400">
                -ZTA
              </span>
            </div>
          </div>

          <div className="hidden items-center gap-8 md:flex">
            <a
              href="#features"
              className="text-sm text-gray-400 transition-colors hover:text-white"
            >
              Features
            </a>
            <a
              href="#architecture"
              className="text-sm text-gray-400 transition-colors hover:text-white"
            >
              Architecture
            </a>
            <a
              href="#portals"
              className="text-sm text-gray-400 transition-colors hover:text-white"
            >
              Portals
            </a>
            <a
              href="#research"
              className="text-sm text-gray-400 transition-colors hover:text-white"
            >
              Research
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
              className="rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/20 transition-all hover:shadow-indigo-500/30 hover:brightness-110"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* ── Hero Section ──────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-20 pt-20 md:pt-32">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="animate-fade-in mb-8 inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-sm text-indigo-300">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Research Prototype — IEEE/Springer Publication Ready</span>
          </div>

          {/* Headline */}
          <h1 className="animate-slide-up text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
            <span className="text-white">Zero Trust </span>
            <span className="gradient-text">Explainable AI</span>
            <br />
            <span className="text-white">for </span>
            <span className="text-gray-400">Judicial Decision Support</span>
          </h1>

          {/* Subtitle */}
          <p className="animate-slide-up delay-200 mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-400 opacity-0 md:text-xl">
            A production-quality framework combining continuous identity
            verification, SHAP-based AI explanations, retrieval-augmented
            generation, and tamper-evident audit ledger for transparent justice.
          </p>

          {/* CTA Buttons */}
          <div className="animate-slide-up delay-300 mt-10 flex flex-col items-center justify-center gap-4 opacity-0 sm:flex-row">
            <Link
              href="/register"
              className="group flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 px-8 py-3.5 text-base font-semibold text-white shadow-xl shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:brightness-110"
            >
              Launch Platform
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <a
              href="#architecture"
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-8 py-3.5 text-base font-medium text-gray-300 backdrop-blur transition-all hover:border-white/20 hover:bg-white/10 hover:text-white"
            >
              View Architecture
              <ChevronRight className="h-4 w-4" />
            </a>
          </div>

          {/* Stats */}
          <div className="animate-slide-up delay-400 mx-auto mt-16 grid max-w-3xl grid-cols-2 gap-8 opacity-0 md:grid-cols-4">
            {[
              { label: "System Modules", value: "23+" },
              { label: "Security Layers", value: "9" },
              { label: "API Endpoints", value: "50+" },
              { label: "DB Tables", value: "17" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl font-bold text-white md:text-3xl">
                  {stat.value}
                </div>
                <div className="mt-1 text-xs text-gray-500 md:text-sm">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features Section ──────────────────────────── */}
      <section id="features" className="relative z-10 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">
              Four Pillars of
              <span className="gradient-text"> Trusted AI</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-400">
              Every design decision is driven by the intersection of security,
              transparency, intelligence, and accountability.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: Shield,
                title: "Zero Trust Security",
                description:
                  "Continuous verification on every request. RBAC + ABAC hybrid policy engine. Never trust, always verify.",
                gradient: "from-indigo-500 to-purple-500",
                glow: "shadow-indigo-500/10",
              },
              {
                icon: Brain,
                title: "Explainable AI",
                description:
                  "SHAP-based feature importance. Natural language explanations. Trust and confidence scoring with full transparency.",
                gradient: "from-cyan-500 to-blue-500",
                glow: "shadow-cyan-500/10",
              },
              {
                icon: FileSearch,
                title: "RAG Pipeline",
                description:
                  "FAISS vector search over legal documents. Citation support. Context-aware prompt building with source verification.",
                gradient: "from-emerald-500 to-teal-500",
                glow: "shadow-emerald-500/10",
              },
              {
                icon: LinkIcon,
                title: "Audit Ledger",
                description:
                  "SHA-256 hash chaining. Merkle tree integrity. ECDSA signatures. Tamper detection with forensic precision.",
                gradient: "from-amber-500 to-orange-500",
                glow: "shadow-amber-500/10",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className={`card card-glow group relative overflow-hidden p-6 ${feature.glow}`}
              >
                {/* Icon */}
                <div
                  className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feature.gradient} shadow-lg`}
                >
                  <feature.icon className="h-6 w-6 text-white" />
                </div>

                {/* Content */}
                <h3 className="mb-2 text-lg font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-gray-400">
                  {feature.description}
                </p>

                {/* Hover glow effect */}
                <div
                  className={`absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gradient-to-br ${feature.gradient} opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-10`}
                />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Architecture Section ──────────────────────── */}
      <section
        id="architecture"
        className="relative z-10 border-y border-white/5 bg-[#0d0d14] py-24"
      >
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">
              Production-Grade
              <span className="gradient-text"> Architecture</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-400">
              Clean Architecture with SOLID principles. Every module is
              independently testable, documented, and deployable.
            </p>
          </div>

          {/* Architecture visualization */}
          <div className="mx-auto max-w-4xl">
            <div className="glass rounded-2xl p-8">
              {/* Frontend Layer */}
              <div className="mb-6">
                <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-indigo-400">
                  Frontend Layer
                </div>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  {[
                    "Citizen Portal",
                    "Lawyer Portal",
                    "Judge Dashboard",
                    "Admin Dashboard",
                  ].map((item) => (
                    <div
                      key={item}
                      className="rounded-lg border border-indigo-500/20 bg-indigo-500/5 px-3 py-2 text-center text-sm text-indigo-300"
                    >
                      {item}
                    </div>
                  ))}
                </div>
                <div className="mt-2 text-center text-xs text-gray-500">
                  Next.js 15 • React 19 • TypeScript • TailwindCSS • ShadCN UI
                </div>
              </div>

              {/* Arrow */}
              <div className="my-4 flex justify-center">
                <div className="h-8 w-px bg-gradient-to-b from-indigo-500/50 to-cyan-500/50" />
              </div>

              {/* Backend Layer */}
              <div className="mb-6">
                <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-cyan-400">
                  Backend Layer
                </div>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                  {[
                    { name: "Auth & Zero Trust", icon: Lock },
                    { name: "AI Engine & SHAP", icon: Brain },
                    { name: "RAG Pipeline", icon: FileSearch },
                    { name: "Audit Ledger", icon: LinkIcon },
                    { name: "Case Management", icon: Scale },
                    { name: "Policy Engine", icon: Shield },
                  ].map((item) => (
                    <div
                      key={item.name}
                      className="flex items-center gap-2 rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-3 py-2 text-sm text-cyan-300"
                    >
                      <item.icon className="h-3.5 w-3.5 flex-shrink-0" />
                      {item.name}
                    </div>
                  ))}
                </div>
                <div className="mt-2 text-center text-xs text-gray-500">
                  FastAPI • Python 3.11+ • SQLAlchemy Async • Pydantic
                </div>
              </div>

              {/* Arrow */}
              <div className="my-4 flex justify-center">
                <div className="h-8 w-px bg-gradient-to-b from-cyan-500/50 to-emerald-500/50" />
              </div>

              {/* Data Layer */}
              <div>
                <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-emerald-400">
                  Data & Services Layer
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    "Supabase PostgreSQL",
                    "Supabase Auth",
                    "Groq API (LLM)",
                  ].map((item) => (
                    <div
                      key={item}
                      className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-center text-sm text-emerald-300"
                    >
                      {item}
                    </div>
                  ))}
                </div>
                <div className="mt-2 text-center text-xs text-gray-500">
                  Free-Tier Compatible • Provider-Independent LLM
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Role Portals Section ──────────────────────── */}
      <section id="portals" className="relative z-10 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">
              Access the Platform as
              <span className="gradient-text"> Your Role</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-400">
              Each stakeholder gets a tailored experience designed for their
              workflow and access level.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                role: "Citizen",
                icon: Users,
                description:
                  "File cases, upload documents, track hearing status, and receive notifications.",
                features: [
                  "Case Filing",
                  "Document Upload",
                  "Status Tracking",
                ],
                color: "blue",
              },
              {
                role: "Lawyer",
                icon: Scale,
                description:
                  "Manage cases, conduct AI-powered legal research, and prepare arguments.",
                features: [
                  "Case Management",
                  "Legal Research (RAG)",
                  "Document Prep",
                ],
                color: "purple",
              },
              {
                role: "Judge",
                icon: Eye,
                description:
                  "Review AI recommendations, examine SHAP explanations, and approve judgments.",
                features: [
                  "AI Assistance",
                  "SHAP Explainability",
                  "Human-in-Loop",
                ],
                color: "cyan",
              },
              {
                role: "Admin",
                icon: Shield,
                description:
                  "Manage users, configure policies, audit system integrity, and monitor analytics.",
                features: [
                  "User Management",
                  "Policy Config",
                  "Audit & Ledger",
                ],
                color: "amber",
              },
            ].map((portal) => {
              const colorMap: Record<string, string> = {
                blue: "border-blue-500/20 hover:border-blue-500/40",
                purple: "border-purple-500/20 hover:border-purple-500/40",
                cyan: "border-cyan-500/20 hover:border-cyan-500/40",
                amber: "border-amber-500/20 hover:border-amber-500/40",
              };
              const iconBgMap: Record<string, string> = {
                blue: "from-blue-500 to-blue-600",
                purple: "from-purple-500 to-purple-600",
                cyan: "from-cyan-500 to-cyan-600",
                amber: "from-amber-500 to-amber-600",
              };
              const tagMap: Record<string, string> = {
                blue: "bg-blue-500/10 text-blue-400",
                purple: "bg-purple-500/10 text-purple-400",
                cyan: "bg-cyan-500/10 text-cyan-400",
                amber: "bg-amber-500/10 text-amber-400",
              };
              return (
                <div
                  key={portal.role}
                  className={`card group p-6 ${colorMap[portal.color]}`}
                >
                  <div
                    className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${iconBgMap[portal.color]}`}
                  >
                    <portal.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-white">
                    {portal.role} Portal
                  </h3>
                  <p className="mb-4 text-sm text-gray-400">
                    {portal.description}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {portal.features.map((f) => (
                      <span
                        key={f}
                        className={`rounded-full px-2.5 py-1 text-xs ${tagMap[portal.color]}`}
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Research Section ──────────────────────────── */}
      <section
        id="research"
        className="relative z-10 border-t border-white/5 bg-[#0d0d14] py-24"
      >
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">
              Built for
              <span className="gradient-text"> Research Publication</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-gray-400">
              Every component is designed with formal models, mathematical
              formulations, and reproducible methodology suitable for
              IEEE/Springer publication.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {[
              {
                title: "Formal Models",
                items: [
                  "Threat Model (STRIDE)",
                  "Trust Score Formula",
                  "Risk Assessment Model",
                  "Access Control Model",
                ],
              },
              {
                title: "Algorithms",
                items: [
                  "Merkle Tree Construction",
                  "Hash Chain Verification",
                  "Trust Score Computation",
                  "Complexity Analysis",
                ],
              },
              {
                title: "Reproducibility",
                items: [
                  "Docker Compose Setup",
                  "Synthetic Test Data",
                  "Automated Test Suite",
                  "Environment Variables",
                ],
              },
            ].map((section) => (
              <div key={section.title} className="card p-6">
                <h3 className="mb-4 text-lg font-semibold text-white">
                  <BarChart3 className="mb-2 h-5 w-5 text-indigo-400" />
                  {section.title}
                </h3>
                <ul className="space-y-2">
                  {section.items.map((item) => (
                    <li
                      key={item}
                      className="flex items-center gap-2 text-sm text-gray-400"
                    >
                      <ChevronRight className="h-3 w-3 text-indigo-400" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="relative z-10 border-t border-white/5 py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2">
              <Scale className="h-5 w-5 text-indigo-400" />
              <span className="text-sm font-medium text-white">Nyaya-ZTA</span>
              <span className="text-sm text-gray-500">
                — Research Prototype
              </span>
            </div>
            <p className="text-sm text-gray-500">
              Built for research. Designed for publication. Engineered for
              production.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
