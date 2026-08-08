"""
VADP Access Policy & Decision Models
=========================================

SQLAlchemy 2.x models for storing ABAC/RBAC Access Policies and Access Audit Decisions.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class AccessPolicy(Base, UUIDMixin, TimestampMixin):
    """
    ABAC + RBAC policy model storing policy conditions, allowed roles, resource type, and action.
    """

    __tablename__ = "access_policies"

    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    allowed_roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)


class AccessDecision(Base, UUIDMixin, TimestampMixin):
    """
    Audit record of every authorization evaluation decision (allow/deny).
    """

    __tablename__ = "access_decisions"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # 'allow' or 'deny'
    policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("access_policies.id"), nullable=True)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trust_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
