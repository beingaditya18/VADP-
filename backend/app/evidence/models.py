"""
Nyaya-ZTA Evidence Record Model
===============================

SQLAlchemy 2.x model for evidence records and chain of custody logs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class EvidenceRecord(Base, UUIDMixin, TimestampMixin):
    """
    Evidence entity linking a document to a case with verification status and custody audit trail.
    Status: pending, verified, rejected, tampered
    """

    __tablename__ = "evidence_records"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)  # forensic, affidavit, physical_photo, transcript
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    integrity_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    chain_of_custody: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    def __repr__(self) -> str:
        return f"<EvidenceRecord(id={self.id}, doc_id={self.document_id}, status={self.verification_status})>"
