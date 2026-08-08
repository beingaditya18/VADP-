"""
VADP Case Management Models
================================

SQLAlchemy 2.x declarative models for Cases, Case Parties, and Case Timeline Events.
Cross-database compatible (SQLite3 & PostgreSQL).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Date, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Case(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Case model representing judicial filings.
    Statuses: filed, under_review, hearing, judgment, closed, appealed
    Priorities: low, medium, high, critical
    """

    __tablename__ = "cases"

    case_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    case_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="filed", index=True, nullable=False
    )
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)

    filed_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    assigned_judge: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=True
    )
    assigned_lawyer: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    court_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    filing_date: Mapped[date] = mapped_column(
        Date, default=lambda: date.today(), nullable=False
    )
    next_hearing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata_", JSON, default=dict, nullable=False
    )

    # Relationships
    parties: Mapped[list[CaseParty]] = relationship(
        "CaseParty", back_populates="case", cascade="all, delete-orphan"
    )
    events: Mapped[list[CaseEvent]] = relationship(
        "CaseEvent", back_populates="case", cascade="all, delete-orphan"
    )
    hearings: Mapped[list[HearingSchedule]] = relationship(
        "HearingSchedule", back_populates="case", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Case(id={self.id}, case_number={self.case_number}, status={self.status})>"


class HearingSchedule(Base, UUIDMixin, TimestampMixin):
    """
    Court hearing schedules with courtroom location, purpose, judge notes, and status.
    """

    __tablename__ = "hearing_schedules"

    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    scheduled_date: Mapped[datetime] = mapped_column(
        String(50), nullable=False
    )  # ISO string or datetime
    courtroom: Mapped[str] = mapped_column(
        String(100), default="Courtroom 1", nullable=False
    )
    hearing_type: Mapped[str] = mapped_column(
        String(100), default="Initial Hearing", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="SCHEDULED", nullable=False
    )  # SCHEDULED, COMPLETED, ADJOURNED, CANCELLED
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    judge_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    # Relationship
    case: Mapped[Case] = relationship("Case", back_populates="hearings")

    def __repr__(self) -> str:
        return f"<HearingSchedule(id={self.id}, case_id={self.case_id}, date={self.scheduled_date})>"


class CaseParty(Base, UUIDMixin, TimestampMixin):
    """
    Parties involved in a case (petitioner, respondent, witness, intervener).
    """

    __tablename__ = "case_parties"

    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    party_name: Mapped[str] = mapped_column(String(255), nullable=False)
    party_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # petitioner, respondent, witness, intervener

    # Relationship
    case: Mapped[Case] = relationship("Case", back_populates="parties")

    def __repr__(self) -> str:
        return (
            f"<CaseParty(id={self.id}, name={self.party_name}, type={self.party_type})>"
        )


class CaseEvent(Base, UUIDMixin, TimestampMixin):
    """
    Timeline audit event logged for case lifecycle milestones.
    """

    __tablename__ = "case_events"

    case_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    event_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationship
    case: Mapped[Case] = relationship("Case", back_populates="events")

    def __repr__(self) -> str:
        return (
            f"<CaseEvent(id={self.id}, type={self.event_type}, case_id={self.case_id})>"
        )
