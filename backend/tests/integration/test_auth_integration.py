"""
Integration tests for Authentication & Token Revocation Workflows.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from app.auth.token_blacklist import TokenBlacklistService


@pytest.fixture(autouse=True)
def clear_token_blacklist():
    TokenBlacklistService.clear()
    yield
    TokenBlacklistService.clear()


class TestAuthenticationIntegration:
    """Integration test suite for full authentication, session management, and logout token revocation."""

    @pytest.mark.asyncio
    async def test_full_register_login_access_logout_cycle(self, async_client: AsyncClient) -> None:
        """
        Test register -> access -> logout -> verify token is invalid after logout.
        """
        # 1. Register new user
        reg_payload = {
            "email": "judicial.officer@nyaya.gov.in",
            "password": "SecurePassword123!",
            "full_name": "Judicial Officer Test",
            "role": "judge",
        }
        reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        token = reg_data["access_token"]
        refresh_token = reg_data["refresh_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Access protected endpoint - should succeed
        me_res = await async_client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "judicial.officer@nyaya.gov.in"

        # 3. Perform logout
        logout_res = await async_client.post("/api/v1/auth/logout", headers=headers)
        assert logout_res.status_code == 200
        assert logout_res.json()["message"] == "Successfully logged out and revoked token."

        # 4. Try accessing protected endpoint with same token - MUST fail with 401 Unauthorized
        revoked_access_res = await async_client.get("/api/v1/auth/me", headers=headers)
        assert revoked_access_res.status_code == 401
        assert "revoked" in revoked_access_res.text.lower() or "invalid" in revoked_access_res.text.lower()

    @pytest.mark.asyncio
    async def test_token_refresh_workflow(self, async_client: AsyncClient) -> None:
        """
        Test exchanging a valid refresh token for a new access token.
        """
        # Register user
        reg_payload = {
            "email": "refresh.user@nyaya.in",
            "password": "Password123!",
            "full_name": "Refresh User",
            "role": "citizen",
        }
        reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
        refresh_token = reg_res.json()["refresh_token"]

        # Request new token
        refresh_res = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_res.status_code == 200
        new_data = refresh_res.json()
        assert "access_token" in new_data
        assert "refresh_token" in new_data

        # Verify new access token works
        new_headers = {"Authorization": f"Bearer {new_data['access_token']}"}
        me_res = await async_client.get("/api/v1/auth/me", headers=new_headers)
        assert me_res.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_login_sessions_and_selective_revocation(self, async_client: AsyncClient) -> None:
        """
        Test that logging in twice issues distinct access tokens and revoking one token leaves other sessions unharmed.
        """
        # Register
        user_info = {
            "email": "multi.session@nyaya.in",
            "password": "MultiSessionPassword123!",
            "full_name": "Multi Session User",
            "role": "lawyer",
        }
        await async_client.post("/api/v1/auth/register", json=user_info)

        # Login Session 1
        login1 = await async_client.post("/api/v1/auth/login", json={
            "email": user_info["email"],
            "password": user_info["password"],
        })
        token1 = login1.json()["access_token"]

        # Login Session 2
        login2 = await async_client.post("/api/v1/auth/login", json={
            "email": user_info["email"],
            "password": user_info["password"],
        })
        token2 = login2.json()["access_token"]

        assert token1 != token2

        # Logout Session 1
        await async_client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token1}"})

        # Token 1 should be revoked
        res1 = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert res1.status_code == 401

        # Token 2 should still be valid
        res2 = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert res2.status_code == 200
