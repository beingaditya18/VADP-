"""
VADP Authorization Service
================================

Service managing policy creation, retrieval, and executing access evaluations with decision logging.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.authorization.models import AccessDecision, AccessPolicy
from app.authorization.policy_engine import PolicyEngine
from app.authorization.schemas import (
    AccessDecisionResponse,
    AccessEvaluationRequest,
    PolicyCreateSchema,
    PolicyResponseSchema,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthorizationService:
    """Service managing access policies and executing Policy Enforcement Point decisions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_policy(self, schema: PolicyCreateSchema) -> PolicyResponseSchema:
        """Create and store a new access policy."""
        policy = AccessPolicy(
            policy_name=schema.policy_name,
            description=schema.description,
            resource_type=schema.resource_type.lower(),
            action=schema.action.lower(),
            conditions=schema.conditions,
            allowed_roles=schema.allowed_roles,
            priority=schema.priority,
            is_active=schema.is_active,
        )
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        logger.info(
            "Created access policy", extra={"policy_id": policy.id, "name": policy.policy_name}
        )
        return PolicyResponseSchema.model_validate(policy)

    async def list_policies(self) -> list[PolicyResponseSchema]:
        """List all stored access policies."""
        result = await self.db.execute(select(AccessPolicy).order_by(AccessPolicy.priority.desc()))
        policies = result.scalars().all()
        return [PolicyResponseSchema.model_validate(p) for p in policies]

    async def evaluate_access(
        self, user: User, request: AccessEvaluationRequest
    ) -> AccessDecisionResponse:
        """
        Evaluate access decision for a user request against stored policies,
        and log the decision to access_decisions table for Zero Trust audit.
        """
        # Fetch active policies for this resource and action
        result = await self.db.execute(
            select(AccessPolicy).where(AccessPolicy.is_active == True)  # noqa: E712
        )
        policies = result.scalars().all()

        allowed, reason, matched_policy = PolicyEngine.evaluate(
            user=user,
            action=request.action,
            resource_type=request.resource_type,
            policies=list(policies),
            context=request.context,
        )

        decision_str = "allow" if allowed else "deny"

        # Record decision in database audit log
        audit_record = AccessDecision(
            user_id=user.id,
            resource_type=request.resource_type,
            resource_id=request.context.resource_id,
            action=request.action,
            decision=decision_str,
            policy_id=matched_policy.id if matched_policy else None,
            context=request.context.model_dump(),
            risk_score=request.context.risk_score,
            trust_score=request.context.trust_score,
            reason=reason,
        )
        self.db.add(audit_record)

        return AccessDecisionResponse(
            allowed=allowed,
            decision=decision_str,
            reason=reason,
            policy_name=matched_policy.policy_name if matched_policy else None,
            risk_score=request.context.risk_score,
            trust_score=request.context.trust_score,
        )
