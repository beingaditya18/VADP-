"""
VADP Distributed Rate Limiter Module
===========================================

Implements Redis-backed sliding window rate limiting for FastAPI.
Protects REST endpoints against denial-of-service (DoS) bursts and key exhaustion attacks.
Features graceful fallback to an in-memory token bucket if Redis is unreachable.
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)

# Fallback in-memory rate limiting store: ip -> list of timestamps
_in_memory_store: dict[str, list[float]] = defaultdict(list)


class RedisRateLimiter:
    """Sliding-window rate limiter utilizing Redis or in-memory fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.max_requests = self.settings.RATE_LIMIT_REQUESTS
        self.window_seconds = self.settings.RATE_LIMIT_WINDOW_SECONDS
        self._redis_client = None
        self._init_redis()

    def _init_redis(self) -> None:
        """Attempt connection to Redis instance."""
        try:
            import redis
            self._redis_client = redis.Redis.from_url(
                self.settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.0,
            )
            self._redis_client.ping()
            logger.info("Connected to Redis for rate limiting at %s", self.settings.REDIS_URL)
        except Exception as e:
            self._redis_client = None
            logger.info("Redis unavailable for rate limiting (%s); falling back to in-memory store.", e)

    def is_rate_limited(self, identifier: str) -> tuple[bool, int, int]:
        """
        Check if identifier has exceeded rate limit within sliding window.
        Returns: (is_limited, remaining_requests, reset_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds

        if self._redis_client:
            try:
                key = f"rate_limit:{identifier}"
                pipeline = self._redis_client.pipeline()
                pipeline.zremrangebyscore(key, 0, window_start)
                pipeline.zadd(key, {str(now): now})
                pipeline.zcard(key)
                pipeline.expire(key, self.window_seconds)
                results = pipeline.execute()

                current_count = results[2]
                remaining = max(0, self.max_requests - current_count)
                reset_in = self.window_seconds

                return current_count > self.max_requests, remaining, reset_in
            except Exception as e:
                logger.warning("Redis rate limit check error: %s; using in-memory fallback.", e)
                self._redis_client = None

        # Fallback to in-memory sliding window
        timestamps = _in_memory_store[identifier]
        _in_memory_store[identifier] = [t for t in timestamps if t > window_start]
        _in_memory_store[identifier].append(now)

        current_count = len(_in_memory_store[identifier])
        remaining = max(0, self.max_requests - current_count)
        reset_in = self.window_seconds

        return current_count > self.max_requests, remaining, reset_in


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware enforcing sliding window rate limits per client IP."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self.limiter = RedisRateLimiter()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Exclude health check and documentation endpoints from rate limits
        path = request.url.path
        if path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        identifier = f"{client_ip}:{path}"

        is_limited, remaining, reset_in = self.limiter.is_rate_limited(identifier)

        if is_limited:
            logger.warning("Rate limit exceeded for client %s on %s", client_ip, path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Too many requests. Please wait before retrying.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                },
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(self.limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_in),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_in)
        return response
