"""
Nyaya-ZTA Middleware Stack
==========================

Provides middleware components for the FastAPI application:
  - CORSMiddleware (configured from settings)
  - RequestIDMiddleware (correlation IDs for tracing)
  - RequestLoggingMiddleware (structured request/response logging)
  - RateLimitMiddleware (in-memory token bucket per IP)

Middleware is registered in order in main.py. The order matters:
  1. CORS (outermost — handles preflight before anything else)
  2. RequestID (sets correlation ID for all downstream processing)
  3. RequestLogging (logs request/response with correlation ID)
  4. RateLimit (rejects excessive requests before hitting business logic)
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging import correlation_id_var, get_logger

logger = get_logger(__name__)


# ── Request ID Middleware ─────────────────────────────────────


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Attaches a unique correlation ID to each request.

    The ID is:
      - Generated as a UUID4 (or extracted from X-Request-ID header if present)
      - Stored in a contextvar for use by loggers throughout the request lifecycle
      - Returned in the X-Request-ID response header for client-side tracing
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Use client-provided ID if present, otherwise generate one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Set the correlation ID in the contextvar
        token = correlation_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            correlation_id_var.reset(token)


# ── Request Logging Middleware ────────────────────────────────


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs incoming requests and outgoing responses with timing information.

    Each request is logged with:
      - HTTP method and path
      - Client IP
      - Response status code
      - Processing time in milliseconds

    Health check endpoints are excluded to reduce noise.
    """

    EXCLUDED_PATHS: set[str] = {"/health", "/health/", "/docs", "/openapi.json", "/favicon.ico"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "query_params": str(request.query_params),
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed with unhandled exception",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "exception": str(exc),
                },
                exc_info=True,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            },
        )

        return response


# ── Rate Limiting Middleware ──────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory token bucket rate limiter per client IP.

    Each IP gets a bucket with a configurable number of tokens that
    refill at a fixed rate. When the bucket is empty, requests are
    rejected with HTTP 429.

    This is suitable for single-instance deployments (free-tier hosting).
    For multi-instance deployments, replace with Redis-backed rate limiting.

    Configuration:
      - max_requests: Maximum number of tokens in the bucket.
      - window_seconds: Time window for token refill.
    """

    def __init__(
        self,
        app: Any,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"tokens": max_requests, "last_refill": time.monotonic()}
        )

    def _refill_tokens(self, bucket: dict[str, Any]) -> None:
        """Refill tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - bucket["last_refill"]
        refill_rate = self.max_requests / self.window_seconds
        new_tokens = elapsed * refill_rate
        bucket["tokens"] = min(self.max_requests, bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/health/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        bucket = self._buckets[client_ip]
        self._refill_tokens(bucket)

        if bucket["tokens"] < 1:
            logger.warning(
                "Rate limit exceeded",
                extra={"client_ip": client_ip, "path": request.url.path},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        bucket["tokens"] -= 1

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, int(bucket["tokens"])))
        response.headers["X-RateLimit-Reset"] = str(self.window_seconds)

        return response
