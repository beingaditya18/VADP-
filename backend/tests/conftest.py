"""
Nyaya-ZTA Test Configuration
==============================

Shared pytest fixtures for unit and integration tests.
Provides:
  - Test settings with overrides
  - Database table initialization
  - Async test client for API testing
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

TEST_DB_FILE = Path(__file__).parent / "test_nyaya.db"

# Set test environment BEFORE importing app modules
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-nyaya-zta-testing-only-12345"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE.as_posix()}"
os.environ["LLM_API_KEY"] = "test-llm-key"
os.environ["LOG_LEVEL"] = "WARNING"

from app.config import Settings, get_settings
from app.db.base import Base
from app.db.engine import get_async_engine
from app.main import create_app

# Import all models to ensure metadata registration
from app.auth.models import *  # noqa: F401, F403
from app.authorization.models import *  # noqa: F401, F403


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test settings with safe defaults."""
    get_settings.cache_clear()
    return get_settings()


@pytest_asyncio.fixture(autouse=True)
async def init_test_database() -> AsyncGenerator[None, None]:
    """
    Auto-fixture that creates all database tables before each test
    and drops them after to ensure test isolation.
    """
    engine = get_async_engine()

    # Import all models to ensure metadata is populated
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for API testing.

    Creates a fresh FastAPI app instance and an httpx AsyncClient
    that sends requests directly to the ASGI app (no network I/O).
    """
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


# ── Unit Test Fixtures ───────────────────────────────────────


@pytest.fixture
def sample_jwt_payload() -> dict:
    """Sample JWT payload for testing."""
    return {
        "sub": "550e8400-e29b-41d4-a716-446655440000",
        "role": "citizen",
        "type": "access",
        "iat": 1700000000,
        "exp": 1700086400,
    }


@pytest.fixture
def sample_user_profile() -> dict:
    """Sample user data."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "citizen",
        "is_active": True,
    }
