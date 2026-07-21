"""
Nyaya-ZTA Audit Ledger Models
=============================

SQLAlchemy 2.x declarative models for Ledger Blocks and Ledger Entries.
Cross-database compatible (SQLite3 & PostgreSQL).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class LedgerBlock(Base, UUIDMixin, TimestampMixin):
    """
    Immutable block in the tamper-evident hash chain.
    """

    __tablename__ = "ledger_blocks"

    block_index: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    data_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    merkle_root: Mapped[str | None] = mapped_column(String(128), nullable=True)
    block_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    signature: Mapped[str | None] = mapped_column(String(512), nullable=True)
    nonce: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    entries_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    entries: Mapped[list[LedgerEntry]] = relationship("LedgerEntry", back_populates="block")

    def __repr__(self) -> str:
        return f"<LedgerBlock(index={self.block_index}, hash={self.block_hash[:8]}...)>"


class LedgerEntry(Base, UUIDMixin, TimestampMixin):
    """
    Individual audit record belonging to a LedgerBlock.
    """

    __tablename__ = "ledger_entries"

    block_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ledger_blocks.id"), index=True, nullable=True)
    entry_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # case_access, document_upload, ai_approval, policy_change
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    data_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    entry_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)

    # Relationship
    block: Mapped[LedgerBlock | None] = relationship("LedgerBlock", back_populates="entries")

    def __repr__(self) -> str:
        return f"<LedgerEntry(id={self.id}, action={self.action}, hash={self.data_hash[:8]}...)>"
