"""
Unit & API Integration tests for Authentication Module.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, decode_jwt, hash_password, verify_password


class TestSecurityUtilities:
    """Test password hashing and JWT token creation/decoding."""

    def test_password_hashing(self) -> None:
        raw_password = "SecretPassword123!"
        hashed = hash_password(raw_password)
        assert hashed != raw_password
        assert verify_password(raw_password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_jwt_generation_and_decoding(self) -> None:
        user_id = "test-user-uuid-1234"
        role = "judge"
        token = create_access_token(user_id=user_id, role=role)

        payload = decode_jwt(token, expected_type="access")
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"


class TestAuthAPI:
    """API endpoints test suite for /api/v1/auth."""

    @pytest.mark.asyncio
    async def test_register_and_login_flow(self, async_client: AsyncClient) -> None:
        # 1. Register new user
        reg_payload = {
            "email": "judge.smith@nyaya.gov.in",
            "password": "SecurePassword123!",
            "full_name": "Justice Smith",
            "role": "judge",
            "court_id": "DEL-HC-01",
        }
        res = await async_client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "judge.smith@nyaya.gov.in"
        assert data["user"]["role"] == "judge"

        token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 2. Access protected profile endpoint /me
        me_res = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["full_name"] == "Justice Smith"

        # 3. Test Refresh Token
        refresh_res = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_res.status_code == 200
        refreshed_data = refresh_res.json()
        assert "access_token" in refreshed_data

        # 4. Test Login with credentials
        login_res = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "judge.smith@nyaya.gov.in",
                "password": "SecurePassword123!",
            },
        )
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, async_client: AsyncClient) -> None:
        login_res = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "judge.smith@nyaya.gov.in",
                "password": "WrongPassword!",
            },
        )
        assert login_res.status_code == 401
