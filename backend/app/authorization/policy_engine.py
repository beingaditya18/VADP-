"""
VADP Hybrid RBAC + ABAC Policy Engine (Policy Decision Point)
===============================================================

Decoupled authorization engine evaluating:
  1. Coarse-grained Role-Based Access Control (RBAC)
  2. Fine-grained Attribute-Based Access Control (ABAC)
  3. Real-time Risk & Trust score evaluation

Returns an explicit allow/deny decision with justification audit trail.
"""

from __future__ import annotations

from typing import Any

from app.auth.models import User
from app.authorization.models import AccessPolicy
from app.authorization.schemas import AuthorizationContextSchema
from app.core.logging import get_logger

logger = get_logger(__name__)


class PolicyEngine:
    """Policy Decision Point (PDP) for Zero Trust Access Control with NIST SP 800-207 Continuous Verification."""

    @staticmethod
    def evaluate(
        user: User,
        action: str,
        resource_type: str,
        policies: list[AccessPolicy],
        context: AuthorizationContextSchema,
    ) -> tuple[bool, str, AccessPolicy | None]:
        """
        Evaluate user and context against a list of active policies (sorted by priority DESC).

        Returns:
            (allowed: bool, reason: str, matching_policy: AccessPolicy | None)
        """
        matching_policies = [
            p
            for p in policies
            if p.is_active
            and p.resource_type.lower() == resource_type.lower()
            and p.action.lower() == action.lower()
        ]

        if not matching_policies:
            # Default Deny principle in Zero Trust
            return (
                False,
                f"Default Deny: No active policy found for {action} on {resource_type}",
                None,
            )

        # Sort by priority descending
        matching_policies.sort(key=lambda p: p.priority, reverse=True)

        for policy in matching_policies:
            # 1. RBAC Check: Is user's role in allowed_roles?
            if policy.allowed_roles and user.role not in policy.allowed_roles:
                continue  # Try next policy

            # 2. ABAC Check: Evaluate conditions dictionary
            abac_passed, abac_reason = PolicyEngine._evaluate_abac_conditions(
                user, context, policy.conditions
            )
            if not abac_passed:
                logger.info(
                    "ABAC evaluation failed for policy",
                    extra={"policy_id": policy.id, "reason": abac_reason, "user_id": user.id},
                )
                continue

            # Policy matched and passed all checks
            return True, f"Access granted by policy '{policy.policy_name}'", policy

        return (
            False,
            "Access denied: Failed role or ABAC attribute conditions across all matching policies",
            None,
        )

    @staticmethod
    def _evaluate_abac_conditions(
        user: User,
        context: AuthorizationContextSchema,
        conditions: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Evaluate attribute-based rules in conditions payload.
        Supported rules:
          - owner_only: True (requires user.id == context.resource_owner_id)
          - require_device_trust: True (requires context.device_trusted == True)
          - max_risk_score: float (requires context.risk_score <= threshold)
          - min_trust_score: float (requires context.trust_score >= threshold)
        """
        if not conditions:
            return True, "No ABAC constraints"

        if conditions.get("owner_only") is True:
            if not context.resource_owner_id or user.id != context.resource_owner_id:
                return False, "User is not the owner of this resource"

        if conditions.get("require_device_trust") is True:
            if not context.device_trusted:
                return False, "Untrusted device rejected by policy"

        max_risk = conditions.get("max_risk_score")
        if max_risk is not None and context.risk_score > float(max_risk):
            return False, f"Risk score ({context.risk_score}) exceeds policy threshold ({max_risk})"

        min_trust = conditions.get("min_trust_score")
        if min_trust is not None and context.trust_score < float(min_trust):
            return False, f"Trust score ({context.trust_score}) below policy minimum ({min_trust})"

        return True, "ABAC constraints passed"
