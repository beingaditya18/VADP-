"""
Nyaya-ZTA Monitoring & Health Checks
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

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db_session

logger = get_logger(__name__)

router = APIRouter(tags=["monitoring"])

_startup_time = datetime.now(timezone.utc)


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
