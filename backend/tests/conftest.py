"""
VADP Test Configuration
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
if TEST_DB_FILE.exists():
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

# Set test environment BEFORE importing app modules
os.environ["ENVIRONMENT"] = "testing"
os.environ["APP_NAME"] = "VADP"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-VADP-testing-only-12345"
os.environ["JWT_ALGORITHM"] = "ES256"
os.environ["JWT_PRIVATE_KEY_PATH"] = str(Path(__file__).parent / "test_jwt_key.pem")
os.environ["JWT_PUBLIC_KEY_PATH"] = str(Path(__file__).parent / "test_jwt_key_pub.pem")
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
from app.cases.models import *  # noqa: F401, F403
from app.documents.models import *  # noqa: F401, F403
from app.evidence.models import *  # noqa: F401, F403
from app.ledger.models import *  # noqa: F401, F403
from app.rag.models import *  # noqa: F401, F403
from app.ai.models import *  # noqa: F401, F403
from app.notifications.models import *  # noqa: F401, F403
from app.vadp.models import *  # noqa: F401, F403


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test settings with safe defaults."""
    get_settings.cache_clear()
    return get_settings()


@pytest_asyncio.fixture(autouse=True)
async def init_test_database() -> AsyncGenerator[None, None]:
    """
    Auto-fixture that creates all database tables before each test.
    """
    engine = get_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh SQLAlchemy AsyncSession for integration tests."""
    from app.db.session import get_session_factory
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


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
