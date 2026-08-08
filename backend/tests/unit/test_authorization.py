"""
Unit & API Integration tests for Authorization Module (RBAC + ABAC Policy Engine).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.auth.models import User
from app.authorization.models import AccessPolicy
from app.authorization.policy_engine import PolicyEngine
from app.authorization.schemas import AuthorizationContextSchema


class TestPolicyEngine:
    """Unit test suite for PDP Policy Engine evaluation logic."""

    def test_default_deny_when_no_policies(self) -> None:
        user = User(id="user-1", email="citizen@nyaya.in", role="citizen")
        ctx = AuthorizationContextSchema()
        allowed, reason, policy = PolicyEngine.evaluate(
            user=user,
            action="read",
            resource_type="case",
            policies=[],
            context=ctx,
        )
        assert allowed is False
        assert "Default Deny" in reason

    def test_admin_evaluated_against_policies_no_bypass(self) -> None:
        admin_user = User(id="admin-1", email="admin@nyaya.in", role="admin")
        ctx = AuthorizationContextSchema()
        # Admin without explicit policy should be subject to Default Deny (No bypass)
        allowed, reason, _ = PolicyEngine.evaluate(
            user=admin_user,
            action="delete",
            resource_type="case",
            policies=[],
            context=ctx,
        )
        assert allowed is False
        assert "Default Deny" in reason

        # Admin with policy permitting admin role should be granted
        admin_policy = AccessPolicy(
            id="policy-admin",
            policy_name="Admin Delete Case",
            resource_type="case",
            action="delete",
            allowed_roles=["admin"],
            is_active=True,
            priority=10,
        )
        allowed, reason, matched = PolicyEngine.evaluate(
            user=admin_user,
            action="delete",
            resource_type="case",
            policies=[admin_policy],
            context=ctx,
        )
        assert allowed is True
        assert matched is not None

    def test_rbac_and_abac_owner_rule(self) -> None:
        citizen_user = User(id="citizen-100", email="citizen@nyaya.in", role="citizen")
        policy = AccessPolicy(
            id="policy-1",
            policy_name="Citizen Own Case Only",
            resource_type="case",
            action="read",
            allowed_roles=["citizen", "lawyer"],
            conditions={"owner_only": True},
            is_active=True,
            priority=10,
        )

        # Context where citizen is owner
        owner_ctx = AuthorizationContextSchema(resource_owner_id="citizen-100")
        allowed, reason, matched = PolicyEngine.evaluate(
            user=citizen_user,
            action="read",
            resource_type="case",
            policies=[policy],
            context=owner_ctx,
        )
        assert allowed is True
        assert matched is not None

        # Context where citizen is NOT owner
        other_ctx = AuthorizationContextSchema(resource_owner_id="other-user-999")
        allowed_other, reason_other, _ = PolicyEngine.evaluate(
            user=citizen_user,
            action="read",
            resource_type="case",
            policies=[policy],
            context=other_ctx,
        )
        assert allowed_other is False


class TestAuthorizationAPI:
    """Test policy administration and access evaluation API endpoints."""

    @pytest.mark.asyncio
    async def test_policy_creation_and_evaluation(self, async_client: AsyncClient) -> None:
        # 1. Register admin user
        admin_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "sysadmin@nyaya.gov.in",
                "password": "AdminPassword123!",
                "full_name": "System Administrator",
                "role": "admin",
            },
        )
        admin_token = admin_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Create policy rule
        policy_payload = {
            "policy_name": "Judge Review Access",
            "resource_type": "case",
            "action": "review",
            "allowed_roles": ["admin", "judge"],
            "conditions": {"require_device_trust": True},
            "priority": 5,
        }
        create_res = await async_client.post(
            "/api/v1/authorization/policies",
            json=policy_payload,
            headers=headers,
        )
        assert create_res.status_code == 201

        # 3. Evaluate access endpoint
        eval_res = await async_client.post(
            "/api/v1/authorization/evaluate",
            json={
                "resource_type": "case",
                "action": "review",
                "context": {"device_trusted": True},
            },
            headers=headers,
        )
        assert eval_res.status_code == 200
        assert eval_res.json()["allowed"] is True
