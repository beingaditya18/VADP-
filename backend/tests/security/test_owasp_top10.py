"""
OWASP Top 10 Security Test Suite for VADP.
================================================

Tests defensive boundaries against common web security threats:
  - SQL Injection (A03:2021-Injection)
  - Cross-Site Scripting (A03:2021-Injection / XSS)
  - Broken Authentication & JWT Forgery (A07:2021-Identification & Authentication Failures)
  - Broken Access Control / RBAC Privilege Escalation (A01:2021-Broken Access Control)
  - Input Fuzzing & Parameter Tampering (A04:2021-Insecure Design)
"""

from __future__ import annotations

import base64
import json
import pytest
from httpx import AsyncClient


class TestOWASPTop10Security:
    """Automated security verification suite targeting OWASP Top 10 vulnerabilities."""

    @pytest.mark.asyncio
    async def test_sql_injection_defense(self, async_client: AsyncClient) -> None:
        """
        Verify that SQL injection payloads in authentication and search parameters are safely parameterized.
        """
        sqli_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1 UNION SELECT 1, 'admin', 'password' --",
            "admin'--",
        ]

        for payload in sqli_payloads:
            # 1. Test SQLi in login email
            res = await async_client.post(
                "/api/v1/auth/login",
                json={"email": payload, "password": "password"},
            )
            # Should be 401 Unauthorized or 422 Unprocessable Entity, NEVER 500 Internal Server Error
            assert res.status_code in (401, 422)

            # 2. Test SQLi in search query
            search_res = await async_client.post(
                "/api/v1/search/query",
                json={"query": payload, "top_k": 5},
            )
            # Search service should return results or 200/404, not crash with SQL execution exception
            assert search_res.status_code in (200, 404, 422)

    @pytest.mark.asyncio
    async def test_xss_script_injection_sanitization(self, async_client: AsyncClient) -> None:
        """
        Verify that HTML/JavaScript injection payloads do not cause raw script execution vulnerabilities.
        """
        xss_payload = "<script>alert('xss-vulnerability')</script>"

        # Register user with XSS payload in full_name
        res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "xss.user@nyaya.in",
                "password": "Password123!",
                "full_name": xss_payload,
                "role": "citizen",
            },
        )
        assert res.status_code == 201
        user_data = res.json()["user"]
        # Ensure exact string stored without executing or corrupting server logic
        assert user_data["full_name"] == xss_payload

    @pytest.mark.asyncio
    async def test_jwt_none_algorithm_attack(self, async_client: AsyncClient) -> None:
        """
        Verify that JWTs using 'none' algorithm are rejected with 401 Unauthorized.
        """
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "admin-id", "role": "admin", "type": "access"}).encode()).decode().rstrip("=")
        malicious_token = f"{header}.{payload}."

        res = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {malicious_token}"},
        )
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_rbac_privilege_escalation_defense(self, async_client: AsyncClient) -> None:
        """
        Verify that a regular citizen cannot access admin-only endpoints.
        """
        # Register citizen
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "citizen.attacker@nyaya.in",
                "password": "Password123!",
                "full_name": "Citizen Attacker",
                "role": "citizen",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt to create policy rule (Admin-only endpoint)
        admin_res = await async_client.post(
            "/api/v1/authorization/policies",
            json={
                "policy_name": "Malicious Escalated Policy",
                "resource_type": "case",
                "action": "delete",
                "allowed_roles": ["citizen"],
                "priority": 100,
            },
            headers=headers,
        )
        assert admin_res.status_code == 403
        assert "access denied" in admin_res.text.lower() or "required role" in admin_res.text.lower()

    @pytest.mark.asyncio
    async def test_fuzzing_and_malformed_input_resilience(self, async_client: AsyncClient) -> None:
        """
        Verify API returns clean 422 validation errors when presented with malformed data.
        """
        malformed_payloads = [
            {"email": "not-an-email", "password": ""},
            {"email": 12345, "password": None},
            {"email": "test@nyaya.in", "role": "super_god_mode"},
        ]

        for payload in malformed_payloads:
            res = await async_client.post("/api/v1/auth/register", json=payload)
            assert res.status_code == 422
