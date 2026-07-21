"""
Unit & Integration tests for Notifications module.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestNotificationsAPI:
    """API tests for /api/v1/notifications."""

    async def test_notification_creation_and_read(self, async_client: AsyncClient) -> None:
        # 1. Register User
        user_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "notif.user@nyaya.in",
                "password": "Password123!",
                "full_name": "Notif User",
                "role": "citizen",
            },
        )
        token = user_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get Notifications (empty initially)
        get_res = await async_client.get("/api/v1/notifications", headers=headers)
        assert get_res.status_code == 200
        assert isinstance(get_res.json(), list)
