"""
Nyaya-ZTA Shared Dependencies
==============================

Common FastAPI dependencies used across multiple modules.
These are injected via Depends() in route handlers.
"""

from __future__ import annotations

from app.config import Settings, get_settings


async def get_app_settings() -> Settings:
    """
    Dependency that provides application settings.

    Useful when a route handler needs access to configuration
    without importing the settings module directly.
    """
    return get_settings()
