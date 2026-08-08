"""
VADP Authorization Schemas
===============================

Pydantic schemas for Policy management and Policy Decision Point (PDP) evaluations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyCreateSchema(BaseModel):
    """Schema for creating a new authorization policy."""

    policy_name: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    resource_type: str = Field(..., description="e.g. 'case', 'document', 'ai_recommendation'")
    action: str = Field(..., description="e.g. 'read', 'write', 'approve', 'delete'")
    conditions: dict[str, Any] = Field(default_factory=dict, description="ABAC attribute match rules")
    allowed_roles: list[str] = Field(default_factory=list, description="RBAC allowed roles")
    priority: int = 0
    is_active: bool = True


class PolicyResponseSchema(BaseModel):
    """Schema for authorization policy response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    policy_name: str
    description: str | None
    resource_type: str
    action: str
    conditions: dict[str, Any]
    allowed_roles: list[str]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuthorizationContextSchema(BaseModel):
    """Context parameters sent to Policy Decision Point for ABAC evaluation."""

    resource_id: str | None = None
    resource_owner_id: str | None = None
    ip_address: str | None = None
    device_trusted: bool = True
    time_of_day_hour: int | None = None
    risk_score: float = 0.0
    trust_score: float = 1.0


class AccessEvaluationRequest(BaseModel):
    """Request payload to evaluate access for a resource and action."""

    resource_type: str
    action: str
    context: AuthorizationContextSchema = Field(default_factory=AuthorizationContextSchema)


class AccessDecisionResponse(BaseModel):
    """Result returned by the Policy Decision Point."""

    allowed: bool
    decision: str  # 'allow' or 'deny'
    reason: str
    policy_name: str | None = None
    risk_score: float
    trust_score: float
