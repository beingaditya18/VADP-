// VADP VADP TypeScript Interfaces
// =====================================
// Type definitions for Verifiable AI Decision Provenance (VADP)
// Verification Contracts, Contract Events, and provenance components.

import type { SHAPValue, TrustBreakdown } from "./ai";

// ── Provenance Components ───────────────────────────────────

export interface EvidenceProvenanceItem {
  evidence_id: string;
  integrity_hash: string;
  verification_status: string;
  document_id: string;
  evidence_type: string;
}

export interface RAGProvenanceItem {
  chunk_id: string;
  document_id: string;
  similarity_score: number;
  snippet: string;
}

export interface RAGRetrievalMetadata {
  embedding_model: string;
  top_k: number;
  similarity_threshold: number;
  retrieval_latency_ms: number;
  total_chunks_searched: number;
}

export interface AuthorizationProvenance {
  decision_id: string | null;
  policy_id: string | null;
  result: string;
  reason: string;
  evaluated_at: string | null;
}

export interface HumanReviewRecord {
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  action: string | null;
  notes: string | null;
}

// ── Completeness Invariant ──────────────────────────────────

export interface CompletenessInvariant {
  has_authorization: boolean;
  has_evidence: boolean;
  has_rag_citations: boolean;
  has_shap_explanation: boolean;
  has_trust_score: boolean;
  has_risk_assessment: boolean;
  has_digital_signature: boolean;
  has_merkle_inclusion: boolean;
  has_human_review: boolean;
  overall_complete: boolean;
  missing_components: string[];
}

// ── Contract Event ──────────────────────────────────────────

export interface ContractEvent {
  id: string;
  contract_id: string;
  event_type: string;
  event_order: number;
  actor_id: string | null;
  event_data: Record<string, unknown>;
  event_hash: string;
  parent_hash: string | null;
  timestamp: string;
  duration_ms: number | null;
}

// ── Verification Contract ───────────────────────────────────

export interface VerificationContract {
  id: string;
  contract_version: string;
  case_id: string;
  recommendation_id: string;

  // Provenance
  authorization: AuthorizationProvenance;
  evidence_provenance: EvidenceProvenanceItem[];
  evidence_count: number;
  evidence_verified: number;
  rag_provenance: RAGProvenanceItem[];
  rag_metadata: RAGRetrievalMetadata;

  // Explainability
  shap_values: SHAPValue[];
  feature_importance: Record<string, number>;
  contributing_factors: Array<{
    factor: string;
    impact: string;
    direction: string;
    explanation: string;
  }>;

  // Scores
  trust_score: number;
  trust_breakdown: TrustBreakdown | null;
  risk_score: number;
  risk_level: string;
  risk_features: Array<{
    name: string;
    value: number;
    weight: number;
    contribution: number;
  }>;

  // Review
  human_review: HumanReviewRecord;

  // Cryptographic
  contract_hash: string;
  digital_signature: string | null;
  signing_algorithm: string;
  merkle_leaf_hash: string | null;
  ledger_block_id: string | null;
  merkle_proof: Array<{ position: string; hash: string }> | null;

  // Completeness
  completeness: CompletenessInvariant;
  completeness_status: string;

  // Lifecycle
  generated_at: string;
  finalized_at: string | null;

  // Timeline
  events: ContractEvent[];
}

// ── Verification Result ─────────────────────────────────────

export interface ContractVerificationResult {
  contract_id: string;
  is_valid: boolean;
  hash_valid: boolean;
  signature_valid: boolean;
  merkle_valid: boolean;
  completeness_valid: boolean;
  evidence_integrity_valid: boolean;
  verification_time_ms: number;
  failures: string[];
  verified_at: string;
}

// ── Event Type Labels ───────────────────────────────────────

export const EVENT_TYPE_LABELS: Record<string, string> = {
  authorization: "Authorization Decision",
  evidence_retrieval: "Evidence Retrieval",
  rag_query: "RAG Legal Research",
  llm_generation: "LLM Generation",
  shap_computation: "SHAP Computation",
  trust_risk_scoring: "Trust & Risk Scoring",
  contract_creation: "Contract Creation",
  digital_signature: "Digital Signature",
  merkle_inclusion: "Merkle Inclusion",
  human_review: "Human Review",
  finalization: "Contract Finalization",
};

export const EVENT_TYPE_COLORS: Record<string, string> = {
  authorization: "#8b5cf6",
  evidence_retrieval: "#06b6d4",
  rag_query: "#10b981",
  llm_generation: "#f59e0b",
  shap_computation: "#ec4899",
  trust_risk_scoring: "#6366f1",
  contract_creation: "#14b8a6",
  digital_signature: "#f97316",
  merkle_inclusion: "#a855f7",
  human_review: "#3b82f6",
  finalization: "#22c55e",
};

export const COMPLETENESS_LABELS: Record<string, string> = {
  has_authorization: "Authorization Provenance",
  has_evidence: "Evidence Provenance",
  has_rag_citations: "RAG Citations",
  has_shap_explanation: "SHAP Explanation",
  has_trust_score: "Trust Score",
  has_risk_assessment: "Risk Assessment",
  has_digital_signature: "Digital Signature",
  has_merkle_inclusion: "Merkle Inclusion",
  has_human_review: "Human Review",
};
