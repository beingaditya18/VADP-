"""
Unit & Integration tests for Hybrid Search API.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSearchAPI:
    """API tests for /api/v1/search."""

    async def test_hybrid_search_execution(self, async_client: AsyncClient) -> None:
        # 1. Register User & File Case
        user_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "search.lawyer@nyaya.in",
                "password": "Password123!",
                "full_name": "Advocate Search",
                "role": "lawyer",
            },
        )
        token = user_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        await async_client.post(
            "/api/v1/cases",
            json={"title": "Constitutional Amendment Writ Petition", "case_type": "Constitutional"},
            headers=headers,
        )

        # 2. Execute Hybrid Search
        search_res = await async_client.get("/api/v1/search?q=Constitutional", headers=headers)
        assert search_res.status_code == 200
        data = search_res.json()
        assert data["query"] == "Constitutional"
        assert data["total_results"] >= 1
        assert any(item["category"] == "case" for item in data["items"])
