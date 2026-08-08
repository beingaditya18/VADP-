"""
VADP Distributed Rate Limiter
===================================

High-performance sliding window rate limiter supporting:
  - Redis-backed distributed storage (for multi-server production deployments)
  - Seamless in-memory fallback (for single-instance, offline dev, and test environments)
  - User-based and IP-based rate limit key resolution
  - Rate limit quota, remaining calculation, and reset window tracking
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Tuple

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Optional Redis import
try:
    import redis.asyncio as aioredis

    HAS_REDIS = True
except ImportError:
    aioredis = None  # type: ignore
    HAS_REDIS = False


class DistributedRateLimiter:
    """
    Distributed sliding-window rate limiter engine.
    """

    _redis_client = None
    _in_memory_buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "window_start": time.monotonic()}
    )

    def __init__(self) -> None:
        self.settings = get_settings()
        self.limit = self.settings.RATE_LIMIT_REQUESTS
        self.window_seconds = self.settings.RATE_LIMIT_WINDOW_SECONDS

    @classmethod
    async def get_redis_client(cls):
        """Lazy-initialize Redis client if URL is set and redis module is installed."""
        if not HAS_REDIS or cls._redis_client is False:
            return None
        if cls._redis_client is None:
            settings = get_settings()
            try:
                client = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=0.2,
                )
                await client.ping()
                cls._redis_client = client
            except Exception:
                cls._redis_client = False
                return None
        return cls._redis_client

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> Tuple[bool, int, int, int]:
        """
        Check rate limit quota for a given identifier (user_id or client_ip).

        Returns:
            (allowed: bool, limit: int, remaining: int, reset_seconds: int)
        """
        max_req = limit or self.limit
        window = window_seconds or self.window_seconds
        rate_key = f"ratelimit:{identifier}"

        redis = await self.get_redis_client()
        if redis:
            try:
                pipe = redis.pipeline()
                pipe.incr(rate_key)
                pipe.ttl(rate_key)
                results = await pipe.execute()
                current_count = results[0]
                ttl = results[1]

                if current_count == 1 or ttl == -1:
                    await redis.expire(rate_key, window)
                    ttl = window

                remaining = max(0, max_req - current_count)
                allowed = current_count <= max_req
                reset_sec = ttl if ttl > 0 else window

                return allowed, max_req, remaining, reset_sec
            except Exception:
                DistributedRateLimiter._redis_client = False

        # In-Memory Fallback
        now = time.monotonic()
        bucket = self._in_memory_buckets[rate_key]
        elapsed = now - bucket["window_start"]

        if elapsed >= window:
            bucket["count"] = 1
            bucket["window_start"] = now
            remaining = max_req - 1
            return True, max_req, remaining, window

        bucket["count"] += 1
        current_count = bucket["count"]
        remaining = max(0, max_req - current_count)
        allowed = current_count <= max_req
        reset_sec = int(window - elapsed)

        return allowed, max_req, remaining, max(1, reset_sec)

    @classmethod
    def clear_memory(cls) -> None:
        """Reset in-memory storage (useful between test cases)."""
        cls._in_memory_buckets.clear()
