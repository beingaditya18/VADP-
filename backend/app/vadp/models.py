"""
VADP VADP Models
=====================

SQLAlchemy 2.x declarative models for Verification Contracts and Contract Events.
Cross-database compatible (SQLite3 & PostgreSQL).

The VerificationContract is the central first-class VADP artifact that
cryptographically binds all provenance components of an AI-assisted
judicial recommendation into one independently verifiable object.

The ContractEvent tracks every step in the Decision Provenance Timeline,
forming an internal hash chain within each contract's lifecycle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class VerificationContract(Base, UUIDMixin, TimestampMixin):
    """
    Central VADP artifact — an independently verifiable cryptographic object
    binding authorization, evidence, RAG citations, SHAP explanation, trust score,
    risk assessment, human review, digital signature, and Merkle proof.

    Each VerificationContract has a 1:1 relationship with an AIRecommendation.
    """

    __tablename__ = "verification_contracts"

    # ── Contract Identity ────────────────────────────────────
    contract_version: Mapped[str] = mapped_column(
        String(20), default="1.0.0", server_default="1.0.0", nullable=False
    )

    # ── Binding References ───────────────────────────────────
    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    recommendation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_recommendations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── Authorization Provenance ─────────────────────────────
    authorization_decision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("access_decisions.id"),
        nullable=True,
    )
    authorization_policy_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("access_policies.id"),
        nullable=True,
    )
    authorization_result: Mapped[str] = mapped_column(
        String(20),
        default="allow",
        nullable=False,
    )
    authorization_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── Evidence Provenance ──────────────────────────────────
    evidence_hashes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    evidence_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    evidence_verified: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # ── RAG Provenance ───────────────────────────────────────
    rag_query_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("rag_queries.id"),
        nullable=True,
    )
    rag_citations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    rag_retrieval_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # ── SHAP Explainability ──────────────────────────────────
    shap_values: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    feature_importance: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    contributing_factors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # ── Trust Score ──────────────────────────────────────────
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    trust_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # ── Risk Assessment ──────────────────────────────────────
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_features: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # ── Human Review ─────────────────────────────────────────
    human_review_status: Mapped[str] = mapped_column(
        String(50),
        default="pending_review",
        nullable=False,
    )
    reviewed_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    review_action: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Cryptographic Integrity ──────────────────────────────
    contract_hash: Mapped[str] = mapped_column(
        String(128),
        index=True,
        nullable=False,
    )
    digital_signature: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    signing_algorithm: Mapped[str | None] = mapped_column(
        String(50),
        default="ECDSA-P256-SHA256",
        nullable=True,
    )

    # ── Merkle Inclusion ─────────────────────────────────────
    merkle_leaf_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    ledger_block_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("ledger_blocks.id"),
        nullable=True,
    )
    merkle_proof: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ── Completeness Invariant ───────────────────────────────
    completeness_status: Mapped[str] = mapped_column(
        String(50),
        default="incomplete",
        index=True,
        nullable=False,
    )
    completeness_checks: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # ── Audit Timestamps ─────────────────────────────────────
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    invalidated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    invalidation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────
    events: Mapped[list[ContractEvent]] = relationship(
        "ContractEvent",
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="ContractEvent.event_order",
    )

    def __repr__(self) -> str:
        return (
            f"<VerificationContract("
            f"id={self.id}, "
            f"case_id={self.case_id}, "
            f"hash={self.contract_hash[:8]}..., "
            f"status={self.completeness_status}"
            f")>"
        )


class ContractEvent(Base, UUIDMixin, TimestampMixin):
    """
    Individual step in the Decision Provenance Timeline.

    Each event is hashed and linked to the previous event's hash,
    forming a tamper-evident chain within a single contract's lifecycle.

    Event types follow the VADP decision lifecycle:
      authorization → evidence_retrieval → rag_query → llm_generation →
      shap_computation → trust_risk_scoring → contract_creation →
      digital_signature → merkle_inclusion → human_review → finalization
    """

    __tablename__ = "contract_events"

    contract_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("verification_contracts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    event_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    actor_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )
    event_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    event_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    parent_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ── Relationship ─────────────────────────────────────────
    contract: Mapped[VerificationContract] = relationship(
        "VerificationContract",
        back_populates="events",
    )

    def __repr__(self) -> str:
        return (
            f"<ContractEvent("
            f"id={self.id}, "
            f"contract_id={self.contract_id}, "
            f"type={self.event_type}, "
            f"order={self.event_order}"
            f")>"
        )
