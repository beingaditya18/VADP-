"""
VADP Middleware Stack
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


from app.core.telemetry import TelemetryManager


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs incoming requests and outgoing responses with timing information,
    and updates APM telemetry metrics (in-flight count, status counters, latency histograms).

    Health check endpoints are excluded to reduce noise.
    """

    EXCLUDED_PATHS: set[str] = {
        "/health",
        "/health/",
        "/docs",
        "/openapi.json",
        "/favicon.ico",
    }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip logging and telemetry for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"

        TelemetryManager.increment_in_flight()

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
            duration_sec = time.perf_counter() - start_time
            TelemetryManager.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration_sec,
            )
        except Exception as exc:
            duration_sec = time.perf_counter() - start_time
            TelemetryManager.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration_seconds=duration_sec,
            )
            duration_ms = duration_sec * 1000
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
        finally:
            TelemetryManager.decrement_in_flight()

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

from app.core.rate_limiter import DistributedRateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Distributed sliding window rate limiter middleware supporting Redis & in-memory fallback.

    Extracts user identity from JWT (per-user quota isolation) or falls back to client IP.

    Configuration:
      - max_requests: Maximum number of requests allowed in time window.
      - window_seconds: Time window in seconds.
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
        self.limiter = DistributedRateLimiter()

    def _resolve_identifier(self, request: Request) -> str:
        """Resolve identifier for rate limiting (user ID if authenticated, else IP)."""
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]

        if token:
            try:
                from app.core.security import decode_jwt

                payload = decode_jwt(token, expected_type="access")
                if "sub" in payload:
                    return f"user:{payload['sub']}"
            except Exception:
                pass

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/health/"):
            return await call_next(request)

        identifier = self._resolve_identifier(request)
        allowed, limit, remaining, reset_sec = await self.limiter.check_rate_limit(
            identifier=identifier,
            limit=self.max_requests,
            window_seconds=self.window_seconds,
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={"identifier": identifier, "path": request.url.path},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                },
                headers={
                    "Retry-After": str(reset_sec),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_sec),
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_sec)

        return response
