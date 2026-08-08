"""
VADP Database Base Models
==============================

Declarative base and common mixins for all SQLAlchemy models.

IMPORTANT — Database Portability:
  - UUID primary keys are stored as String(36) for SQLite compatibility.
    PostgreSQL can also use String(36) without issues.
  - JSONB is NOT used. JSON type is used instead (works on both SQLite and PG).
  - All timestamps use DateTime(timezone=True).
  - server_default uses text() expressions that work on both engines.

All domain models should inherit from Base and include the mixins:

    class Case(Base, UUIDMixin, TimestampMixin):
        __tablename__ = "cases"
        ...
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


def generate_uuid() -> str:
    """Generate a UUID4 string. Used as default for UUID primary keys."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """
    Declarative base for all VADP SQLAlchemy models.

    Provides a consistent foundation with type annotation support
    via SQLAlchemy 2.0 mapped_column syntax.
    """

    pass


class UUIDMixin:
    """
    Mixin that provides a UUID primary key as String(36).

    Uses String(36) instead of PostgreSQL-native UUID type for
    cross-database compatibility (SQLite + PostgreSQL).
    UUID is generated in Python via uuid4().
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True,
    )


class TimestampMixin:
    """
    Mixin that provides created_at and updated_at timestamps.

    Timestamps are generated in Python to ensure consistent
    behavior across SQLite and PostgreSQL.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin for soft-delete support.

    Records are never physically deleted; instead, is_deleted is set
    to True and deleted_at is populated. All queries should filter
    on is_deleted = False unless explicitly including deleted records.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
