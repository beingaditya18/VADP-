"""
Security tests for httpOnly Cookie Authentication & Revocation.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from app.auth.token_blacklist import TokenBlacklistService


@pytest.fixture(autouse=True)
def clear_blacklist():
    TokenBlacklistService.clear()
    yield
    TokenBlacklistService.clear()


class TestCookieAuthentication:
    """Security test suite for httpOnly cookie issuance, cookie auth, and cookie deletion on logout."""

    @pytest.mark.asyncio
    async def test_login_issues_httponly_cookies(self, async_client: AsyncClient) -> None:
        """
        Verify that login sets access_token as an httpOnly cookie.
        """
        # Register
        reg_payload = {
            "email": "cookie.user@nyaya.in",
            "password": "Password123!",
            "full_name": "Cookie User",
            "role": "judge",
        }
        await async_client.post("/api/v1/auth/register", json=reg_payload)

        # Login
        login_res = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "cookie.user@nyaya.in", "password": "Password123!"},
        )
        assert login_res.status_code == 200
        set_cookie_headers = login_res.headers.get_list("set-cookie")
        assert any("access_token=" in header for header in set_cookie_headers)
        assert any("httponly" in header.lower() for header in set_cookie_headers)

    @pytest.mark.asyncio
    async def test_authenticated_request_via_httponly_cookie(self, async_client: AsyncClient) -> None:
        """
        Verify that passing access_token in cookies (without Authorization header) successfully authenticates user.
        """
        # Register and get token
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "cookie.auth@nyaya.in",
                "password": "Password123!",
                "full_name": "Cookie Auth User",
                "role": "citizen",
            },
        )
        token = reg_res.json()["access_token"]

        # Call GET /auth/me WITH cookie, WITHOUT Authorization header
        me_res = await async_client.get(
            "/api/v1/auth/me",
            cookies={"access_token": token},
        )
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "cookie.auth@nyaya.in"

    @pytest.mark.asyncio
    async def test_logout_deletes_cookies_and_revokes_token(self, async_client: AsyncClient) -> None:
        """
        Verify that logging out clears access_token cookie and revokes token in blacklist.
        """
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout.cookie@nyaya.in",
                "password": "Password123!",
                "full_name": "Logout Cookie User",
                "role": "lawyer",
            },
        )
        token = reg_res.json()["access_token"]

        # Logout passing cookie
        logout_res = await async_client.post(
            "/api/v1/auth/logout",
            cookies={"access_token": token},
        )
        assert logout_res.status_code == 200
        set_cookie_headers = logout_res.headers.get_list("set-cookie")
        assert any("access_token=" in header for header in set_cookie_headers)

        # Subsequent request with revoked cookie must be rejected with 401
        rejected_res = await async_client.get(
            "/api/v1/auth/me",
            cookies={"access_token": token},
        )
        assert rejected_res.status_code == 401
