"""
VADP VADP Schemas
======================

Pydantic schemas for Verification Contracts, Contract Events,
provenance components, completeness invariants, and independent
verification results.

All schemas use ConfigDict(from_attributes=True) for seamless
SQLAlchemy model ↔ Pydantic schema conversion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ai.schemas import (
    ContributingFactorSchema,
    RiskFeatureSchema,
    SHAPValueSchema,
    TrustScoreBreakdownSchema,
)
from app.ledger.schemas import MerkleProofNodeSchema


# ── Provenance Component Schemas ─────────────────────────────


class EvidenceProvenanceItem(BaseModel):
    """Evidence record provenance for Verification Contract binding, supporting redactable Merkle commitments under BSA §63(4)."""

    evidence_id: str
    integrity_hash: str
    verification_status: str
    document_id: str
    evidence_type: str
    is_redacted: bool = False
    redacted_commitment_hash: str | None = None


class RAGProvenanceItem(BaseModel):
    """RAG citation provenance for Verification Contract binding."""

    chunk_id: str
    document_id: str
    similarity_score: float
    snippet: str = Field(default="", max_length=500)


class RAGRetrievalMetadata(BaseModel):
    """RAG retrieval pipeline metadata for reproducibility."""

    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    similarity_threshold: float = 0.3
    retrieval_latency_ms: int = 0
    total_chunks_searched: int = 0
    index_type: str = "IndexFlatIP"  # e.g. 'IndexIVFFlat(nlist=100, nprobe=10)'

    # Field 3: Dense semantic similarity Sim(Q, Cj) — Semantic Precedent Relator
    semantic_similarity: float = 0.0

    # Field 4: Statutory section intersection × dense similarity (VADP Precedent Relator)
    statutory_match_score: float = 0.0        # StatutoryMatch(Q, Cj) — Jaccard overlap
    combined_relator_score: float = 0.0       # Sim(Q, Cj) × StatutoryMatch(Q, Cj)


class AuthorizationProvenance(BaseModel):
    """Access control decision provenance for Verification Contract binding."""

    decision_id: str | None = None
    policy_id: str | None = None
    result: str = "allow"
    reason: str = "Default allow — no policy evaluated"
    evaluated_at: datetime | None = None


class HumanReviewRecord(BaseModel):
    """Human-in-the-loop review status for judicial oversight."""

    status: str = "pending_review"
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    action: str | None = None
    notes: str | None = None


# ── Completeness Invariant ───────────────────────────────────


class CompletenessInvariant(BaseModel):
    """
    VADP Completeness Invariant — verifies that all required
    provenance components are present in a Verification Contract.

    A contract is considered 'complete' only when all nine
    verification criteria are satisfied.
    """

    has_authorization: bool = False
    has_evidence: bool = False
    has_rag_citations: bool = False
    has_shap_explanation: bool = False
    has_trust_score: bool = False
    has_risk_assessment: bool = False
    has_digital_signature: bool = False
    has_merkle_inclusion: bool = False
    has_human_review: bool = False
    overall_complete: bool = False
    missing_components: list[str] = Field(default_factory=list)


# ── Contract Event Schema ────────────────────────────────────


class ContractEventSchema(BaseModel):
    """Single step in the Decision Provenance Timeline."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    contract_id: str
    event_type: str
    event_order: int
    actor_id: str | None = None
    event_data: dict[str, Any] = Field(default_factory=dict)
    event_hash: str
    parent_hash: str | None = None
    timestamp: datetime
    duration_ms: int | None = None


# ── Verification Contract Schemas ────────────────────────────


class VerificationContractCreateSchema(BaseModel):
    """Input schema for generating a new Verification Contract."""

    case_id: str
    recommendation_id: str


class VerificationContractResponseSchema(BaseModel):
    """
    Full Verification Contract — the central VADP artifact.

    This is the independently verifiable cryptographic object that
    a judge, auditor, or external party can inspect to verify every
    component of an AI-assisted judicial recommendation without
    needing to trust the AI model itself.
    """

    model_config = ConfigDict(from_attributes=True)

    # Identity
    id: str
    contract_version: str = "1.0.0"
    case_id: str
    recommendation_id: str

    # Authorization Provenance
    authorization: AuthorizationProvenance

    # Evidence Provenance
    evidence_provenance: list[EvidenceProvenanceItem] = Field(default_factory=list)
    evidence_count: int = 0
    evidence_verified: int = 0

    # RAG Provenance
    rag_provenance: list[RAGProvenanceItem] = Field(default_factory=list)
    rag_metadata: RAGRetrievalMetadata = Field(default_factory=RAGRetrievalMetadata)

    # SHAP Explainability
    shap_values: list[SHAPValueSchema] = Field(default_factory=list)
    feature_importance: dict[str, float] = Field(default_factory=dict)
    contributing_factors: list[ContributingFactorSchema] = Field(default_factory=list)

    # Trust Score (Verified)
    trust_score: float
    trust_breakdown: TrustScoreBreakdownSchema | None = None

    # Risk Assessment
    risk_score: float
    risk_level: str
    risk_features: list[RiskFeatureSchema] = Field(default_factory=list)

    # Human Review
    human_review: HumanReviewRecord = Field(default_factory=HumanReviewRecord)

    # Cryptographic Integrity
    contract_hash: str
    digital_signature: str | None = None
    signing_algorithm: str = "ECDSA-P256-SHA256"

    # Merkle Inclusion
    merkle_leaf_hash: str | None = None
    ledger_block_id: str | None = None
    merkle_proof: list[MerkleProofNodeSchema] | None = None

    # Completeness
    completeness: CompletenessInvariant = Field(default_factory=CompletenessInvariant)
    completeness_status: str = "incomplete"

    # Field 7: Generative Text Reliability — Normalized Semantic Self-Consistency Score
    # Computed from 3 LLM completions at T=0.7 via pairwise all-MiniLM-L6-v2 cosine similarity
    generative_reliability_score: float | None = None   # NSSC ∈ [0, 1]
    escalation_required: bool = False  # True when NSSC < 0.82 (mandatory human review)

    # Lifecycle Timestamps
    generated_at: datetime
    finalized_at: datetime | None = None

    # Decision Provenance Timeline
    events: list[ContractEventSchema] = Field(default_factory=list)


class ContractVerificationResultSchema(BaseModel):
    """
    Result of independent verification of a Verification Contract.

    Performs:
      1. SHA-256 contract hash recalculation
      2. ECDSA digital signature verification
      3. Merkle inclusion proof verification
      4. Completeness invariant check
      5. Evidence integrity hash cross-validation
    """

    contract_id: str
    is_valid: bool
    hash_valid: bool
    signature_valid: bool
    merkle_valid: bool
    completeness_valid: bool
    evidence_integrity_valid: bool
    verification_time_ms: float
    failures: list[str] = Field(default_factory=list)
    verified_at: datetime


class ContractListResponseSchema(BaseModel):
    """Paginated list of Verification Contracts."""

    items: list[VerificationContractResponseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class HumanReviewRequestSchema(BaseModel):
    """Input schema for recording human review on a contract."""

    action: str = Field(
        ...,
        description="Review action: 'approved', 'rejected', 'flagged', 'override'",
    )
    notes: str | None = Field(
        default=None,
        description="Optional review notes from the judge",
    )


class HumanOverrideCoverageResponseSchema(BaseModel):
    """Aggregate metric schema for Human Override Coverage."""

    total_contracts: int
    reviewed_contracts: int
    approved_count: int
    rejected_override_count: int
    flagged_count: int
    pending_count: int
    human_override_coverage_pct: float
    review_action_breakdown: dict[str, int] = Field(default_factory=dict)

