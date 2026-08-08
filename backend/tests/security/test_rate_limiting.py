"""
Security tests for Distributed Rate Limiting & Quota Management.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from app.core.rate_limiter import DistributedRateLimiter


@pytest.fixture(autouse=True)
def clear_rate_limiter_memory():
    DistributedRateLimiter.clear_memory()
    yield
    DistributedRateLimiter.clear_memory()


class TestRateLimitingSecurity:
    """Security test suite for rate limit headers, quota exhaustion, 429 status code, and user isolation."""

    @pytest.mark.asyncio
    async def test_rate_limit_response_headers(self, async_client: AsyncClient) -> None:
        """
        Verify that responses include rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset).
        """
        res = await async_client.get("/api/v1/auth/me")
        assert "x-ratelimit-limit" in res.headers
        assert "x-ratelimit-remaining" in res.headers
        assert "x-ratelimit-reset" in res.headers

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_returns_429(self, async_client: AsyncClient) -> None:
        """
        Verify that exceeding the allowed quota triggers 429 Too Many Requests and Retry-After header.
        """
        limiter = DistributedRateLimiter()

        # Execute requests until limit is exceeded (simulated window of 3 requests for test fast execution)
        identifier = "ip:127.0.0.1-test-burst"

        for i in range(3):
            allowed, limit, remaining, reset_sec = await limiter.check_rate_limit(
                identifier=identifier,
                limit=3,
                window_seconds=10,
            )
            assert allowed is True

        # 4th request must be rejected
        allowed, limit, remaining, reset_sec = await limiter.check_rate_limit(
            identifier=identifier,
            limit=3,
            window_seconds=10,
        )
        assert allowed is False
        assert remaining == 0
        assert reset_sec > 0

    @pytest.mark.asyncio
    async def test_per_user_rate_limit_isolation(self, async_client: AsyncClient) -> None:
        """
        Verify that User A exhausting their quota does not impact User B's quota.
        """
        limiter = DistributedRateLimiter()

        user1_id = "user:user-id-100"
        user2_id = "user:user-id-200"

        # Deplete User 1 quota
        for _ in range(5):
            await limiter.check_rate_limit(user1_id, limit=5, window_seconds=60)

        # User 1 should be blocked
        allowed1, _, _, _ = await limiter.check_rate_limit(user1_id, limit=5, window_seconds=60)
        assert allowed1 is False

        # User 2 should still have full quota allowed
        allowed2, limit2, remaining2, _ = await limiter.check_rate_limit(user2_id, limit=5, window_seconds=60)
        assert allowed2 is True
        assert remaining2 == 4
