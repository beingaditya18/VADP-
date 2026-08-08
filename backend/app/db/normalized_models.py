"""
VADP Normalized Legal Database Models
===========================================

Declarative SQLAlchemy 2.0 models for the 13 core normalized legal decision-support entities:
1. Judgment
2. Judge
3. Party
4. Court
5. Statute
6. Precedent
7. Citation
8. LegalIssue
9. EvidenceRecord
10. EmbeddingRecord
11. VerificationContract
12. AuditEvent
13. HumanReview

All models inherit from Base, UUIDMixin, and TimestampMixin for cross-database compatibility (SQLite3 + PostgreSQL).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Court(Base, UUIDMixin, TimestampMixin):
    """Normalized Court Entity (Supreme Court, High Court of Bombay, etc.)"""

    __tablename__ = "courts"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    court_type: Mapped[str] = mapped_column(
        String(100), default="Supreme Court", index=True, nullable=False
    )
    jurisdiction: Mapped[str] = mapped_column(
        String(100), default="Appellate / Original", nullable=False
    )
    location: Mapped[str] = mapped_column(String(150), default="New Delhi, India", nullable=False)
    code: Mapped[str] = mapped_column(String(50), default="INSC", index=True, nullable=False)

    # Relationships
    judgments: Mapped[list[Judgment]] = relationship("Judgment", back_populates="court")
    judges: Mapped[list[Judge]] = relationship("Judge", back_populates="court")

    def __repr__(self) -> str:
        return f"<Court(id={self.id}, name={self.name})>"


class Judge(Base, UUIDMixin, TimestampMixin):
    """Normalized Judge Entity"""

    __tablename__ = "judges"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(150), default="Hon'ble Justice", nullable=False)
    court_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("courts.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    court: Mapped[Court | None] = relationship("Court", back_populates="judges")

    def __repr__(self) -> str:
        return f"<Judge(id={self.id}, name={self.name})>"


class Judgment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Normalized Judgment Entity (350 Real ILDC Cases)"""

    __tablename__ = "judgments"

    case_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    citation: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    decision_date: Mapped[date] = mapped_column(Date, nullable=False)
    legal_category: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )  # Criminal, Civil, etc.
    bench_type: Mapped[str] = mapped_column(String(100), default="Division Bench", nullable=False)
    court_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("courts.id", ondelete="SET NULL"), nullable=True
    )

    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    factual_background: Mapped[str] = mapped_column(Text, nullable=False)
    ratio_decidendi: Mapped[str | None] = mapped_column(Text, nullable=True)

    trust_score: Mapped[float] = mapped_column(Float, default=0.90, index=True, nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(50), default="under_review", index=True, nullable=False
    )

    # Relationships
    court: Mapped[Court | None] = relationship("Court", back_populates="judgments")
    parties: Mapped[list[Party]] = relationship(
        "Party", back_populates="judgment", cascade="all, delete-orphan"
    )
    legal_issues: Mapped[list[LegalIssue]] = relationship(
        "LegalIssue", back_populates="judgment", cascade="all, delete-orphan"
    )
    precedents: Mapped[list[Precedent]] = relationship(
        "Precedent", back_populates="judgment", cascade="all, delete-orphan"
    )
    citations: Mapped[list[Citation]] = relationship(
        "Citation", back_populates="judgment", cascade="all, delete-orphan"
    )
    evidence_records: Mapped[list[EvidenceRecordNorm]] = relationship(
        "EvidenceRecordNorm", back_populates="judgment", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list[EmbeddingRecord]] = relationship(
        "EmbeddingRecord", back_populates="judgment", cascade="all, delete-orphan"
    )
    verification_contracts: Mapped[list[VerificationContractNorm]] = relationship(
        "VerificationContractNorm", back_populates="judgment", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list[AuditEventNorm]] = relationship(
        "AuditEventNorm", back_populates="judgment", cascade="all, delete-orphan"
    )
    human_reviews: Mapped[list[HumanReviewNorm]] = relationship(
        "HumanReviewNorm", back_populates="judgment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Judgment(id={self.id}, case_number={self.case_number}, category={self.legal_category})>"


class Party(Base, UUIDMixin, TimestampMixin):
    """Normalized Case Party Entity"""

    __tablename__ = "parties"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    party_name: Mapped[str] = mapped_column(String(300), nullable=False)
    party_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # petitioner, respondent, appellant, relator
    counsel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="parties")

    def __repr__(self) -> str:
        return f"<Party(id={self.id}, name={self.party_name}, type={self.party_type})>"


class Statute(Base, UUIDMixin, TimestampMixin):
    """Normalized Statutory Provision Entity"""

    __tablename__ = "statutes"

    act_name: Mapped[str] = mapped_column(String(300), index=True, nullable=False)
    section_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    section_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    citations: Mapped[list[Citation]] = relationship("Citation", back_populates="statute")

    def __repr__(self) -> str:
        return f"<Statute(act={self.act_name}, section={self.section_number})>"


class Precedent(Base, UUIDMixin, TimestampMixin):
    """Normalized Precedent Entity"""

    __tablename__ = "precedents"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    cited_title: Mapped[str] = mapped_column(String(500), nullable=False)
    cited_citation: Mapped[str] = mapped_column(String(255), nullable=False)
    treatment: Mapped[str] = mapped_column(
        String(100), default="relied_on", nullable=False
    )  # relied_on, distinguished, overruled
    relevance_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="precedents")
    citations: Mapped[list[Citation]] = relationship("Citation", back_populates="precedent")

    def __repr__(self) -> str:
        return f"<Precedent(title={self.cited_title}, treatment={self.treatment})>"


class Citation(Base, UUIDMixin, TimestampMixin):
    """Normalized Citation Junction Entity"""

    __tablename__ = "citations"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    statute_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("statutes.id", ondelete="SET NULL"), nullable=True
    )
    precedent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("precedents.id", ondelete="SET NULL"), nullable=True
    )
    paragraph_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="citations")
    statute: Mapped[Statute | None] = relationship("Statute", back_populates="citations")
    precedent: Mapped[Precedent | None] = relationship("Precedent", back_populates="citations")


class LegalIssue(Base, UUIDMixin, TimestampMixin):
    """Normalized Legal Questions Framed Entity"""

    __tablename__ = "legal_issues"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_statement: Mapped[str] = mapped_column(Text, nullable=False)
    domain_category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # Relationship
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="legal_issues")


class EvidenceRecordNorm(Base, UUIDMixin, TimestampMixin):
    """Normalized Evidence Record Entity"""

    __tablename__ = "evidence_records_norm"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # judgment_text, affidavit, forensic, gazette
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    integrity_status: Mapped[str] = mapped_column(String(50), default="VERIFIED", nullable=False)
    digital_signature: Mapped[str] = mapped_column(Text, nullable=False)
    merkle_proof: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    chain_of_custody: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Relationship
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="evidence_records")


class EmbeddingRecord(Base, UUIDMixin, TimestampMixin):
    """Normalized Vector Embeddings Entity"""

    __tablename__ = "embeddings_norm"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vector_dim: Mapped[int] = mapped_column(Integer, default=384, nullable=False)

    # Relationship
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="embeddings")


class VerificationContractNorm(Base, UUIDMixin, TimestampMixin):
    """Normalized Verification Contract Entity"""

    __tablename__ = "verification_contracts_norm"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    contract_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    authorization_proof: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evidence_provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    citation_provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    shap_explanation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    digital_signature: Mapped[str] = mapped_column(Text, nullable=False)
    merkle_root_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    merkle_inclusion_proof: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    human_review_status: Mapped[str] = mapped_column(
        String(50), default="pending_review", nullable=False
    )
    completeness_status: Mapped[str] = mapped_column(String(50), default="COMPLETE", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationship
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="verification_contracts")


class AuditEventNorm(Base, UUIDMixin, TimestampMixin):
    """Normalized Chronological Audit Event Entity"""

    __tablename__ = "audit_events_norm"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    parent_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationship
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="audit_events")


class HumanReviewNorm(Base, UUIDMixin, TimestampMixin):
    """Normalized Human Review Entity"""

    __tablename__ = "human_reviews_norm"

    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reviewed_by: Mapped[str] = mapped_column(
        String(255), default="Justice A. K. Sharma", nullable=False
    )
    review_action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # approve, reject_override, flag_review
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    # Relationship
    judgment: Mapped[Judgment] = relationship("Judgment", back_populates="human_reviews")
