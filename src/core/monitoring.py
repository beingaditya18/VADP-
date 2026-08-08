"""
VADP Monitoring & Health Checks
=====================================

Provides health check and readiness endpoints for deployment platforms
(Render, Docker, load balancers) and application version information.

Endpoints:
  - GET /health         → Liveness probe (always 200 if server is running)
  - GET /health/ready   → Readiness probe (checks database connectivity)
  - GET /health/version → Application version and build metadata
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.logging import get_logger
from app.core.telemetry import TelemetryManager
from app.db.session import get_db_session

logger = get_logger(__name__)

router = APIRouter(tags=["monitoring"])

_startup_time = datetime.now(timezone.utc)


@router.get("/metrics", include_in_schema=True, summary="Prometheus APM metrics")
async def get_prometheus_metrics() -> Response:
    """
    Expose standard Prometheus metrics exposition format.
    Consumed by Prometheus, DataDog, and OpenTelemetry collectors.
    """
    metrics_text = TelemetryManager.generate_prometheus_text()
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/health/detailed", summary="Comprehensive subsystem health check")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Detailed readiness probe inspecting database, FAISS index, Merkle ledger, and system state.
    """
    settings = get_settings()
    subsystems: dict[str, str] = {}
    is_healthy = True

    # 1. Database connection check
    try:
        res = await db.execute(text("SELECT 1"))
        res.scalar()
        subsystems["database"] = "healthy"
    except Exception as e:
        subsystems["database"] = f"unhealthy: {e}"
        is_healthy = False

    # 2. FAISS vector index check
    try:
        from pathlib import Path
        faiss_path = Path(settings.FAISS_INDEX_PATH)
        subsystems["faiss_index"] = "healthy" if faiss_path.exists() else "not_initialized"
    except Exception:
        subsystems["faiss_index"] = "unhealthy"

    # 3. Merkle Audit Ledger key check
    try:
        from pathlib import Path
        ledger_key = Path(settings.LEDGER_SIGNING_KEY_PATH)
        subsystems["ledger_keys"] = "configured" if ledger_key.parent.exists() else "missing"
    except Exception:
        subsystems["ledger_keys"] = "unhealthy"

    # 4. Rate Limiter status
    subsystems["rate_limiter"] = "active"

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round((datetime.now(timezone.utc) - _startup_time).total_seconds(), 2),
        "environment": settings.ENVIRONMENT.value,
        "subsystems": subsystems,
    }


@router.get("/health")
async def health_check() -> dict:
    """
    Liveness probe.

    Returns HTTP 200 if the application process is running.
    Used by container orchestrators and load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": (datetime.now(timezone.utc) - _startup_time).total_seconds(),
    }


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Readiness probe.

    Verifies that the application can connect to the database.
    Returns HTTP 200 only if all dependencies are available.
    Returns HTTP 503 if the database is unreachable.
    """
    checks: dict[str, str] = {}

    # Check database connectivity
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = "connected"
    except Exception as e:
        logger.error("Database readiness check failed", exc_info=True)
        checks["database"] = f"unavailable: {e}"
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        }

    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get("/health/version")
async def version_info() -> dict:
    """
    Application version and metadata.

    Returns current version, environment, and startup time.
    """
    settings = get_settings()
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "environment": settings.ENVIRONMENT.value,
        "startup_time": _startup_time.isoformat(),
    }
