"""
Unit tests for the core foundation modules.

Tests:
  - Configuration loading and validation
  - Exception hierarchy and serialization
  - Health check endpoint
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import Environment, Settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    LedgerIntegrityError,
    NotFoundError,
    NyayaBaseException,
    RateLimitError,
    TokenExpiredError,
    TokenInvalidError,
    ValidationError,
)


# ── Configuration Tests ──────────────────────────────────────


class TestSettings:
    """Test suite for application configuration."""

    def test_settings_load_from_env(self, test_settings: Settings) -> None:
        """Settings should load from environment variables."""
        assert test_settings.ENVIRONMENT == Environment.TESTING
        assert test_settings.SUPABASE_URL == "https://test.supabase.co"

    def test_settings_is_testing(self, test_settings: Settings) -> None:
        """is_testing property should return True in test environment."""
        assert test_settings.is_testing is True
        assert test_settings.is_production is False

    def test_cors_origins_parsing(self) -> None:
        """CORS origins should parse comma-separated strings."""
        import os

        os.environ["CORS_ORIGINS"] = "http://a.com, http://b.com"
        from app.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS
        # Reset
        os.environ["CORS_ORIGINS"] = "http://localhost:3000"
        get_settings.cache_clear()


# ── Exception Tests ──────────────────────────────────────────


class TestExceptions:
    """Test suite for exception hierarchy."""

    def test_base_exception_defaults(self) -> None:
        """Base exception should have default status code and message."""
        exc = NyayaBaseException()
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.message == "An unexpected error occurred."

    def test_base_exception_custom_message(self) -> None:
        """Base exception should accept custom message."""
        exc = NyayaBaseException(message="Custom error", detail={"key": "value"})
        assert exc.message == "Custom error"
        assert exc.detail == {"key": "value"}

    def test_exception_to_dict(self) -> None:
        """Exception should serialize to dictionary correctly."""
        exc = AuthenticationError(detail="token expired")
        result = exc.to_dict()
        assert result["error"] is True
        assert result["error_code"] == "AUTH_FAILED"
        assert result["message"] == "Authentication failed."
        assert result["detail"] == "token expired"

    def test_exception_hierarchy(self) -> None:
        """Specific exceptions should inherit from NyayaBaseException."""
        assert issubclass(AuthenticationError, NyayaBaseException)
        assert issubclass(TokenExpiredError, AuthenticationError)
        assert issubclass(TokenInvalidError, AuthenticationError)
        assert issubclass(AuthorizationError, NyayaBaseException)
        assert issubclass(NotFoundError, NyayaBaseException)
        assert issubclass(ValidationError, NyayaBaseException)
        assert issubclass(RateLimitError, NyayaBaseException)
        assert issubclass(LedgerIntegrityError, NyayaBaseException)

    def test_status_codes(self) -> None:
        """Each exception type should have the correct HTTP status code."""
        assert AuthenticationError.status_code == 401
        assert AuthorizationError.status_code == 403
        assert NotFoundError.status_code == 404
        assert ValidationError.status_code == 422
        assert RateLimitError.status_code == 429
        assert LedgerIntegrityError.status_code == 500

    def test_exception_to_dict_without_detail(self) -> None:
        """Serialization should omit detail when not provided."""
        exc = NotFoundError()
        result = exc.to_dict()
        assert "detail" not in result


# ── Health Check Tests ───────────────────────────────────────


class TestHealthCheck:
    """Test suite for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient) -> None:
        """GET /health should return 200 with status healthy."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_version_endpoint(self, async_client: AsyncClient) -> None:
        """GET /health/version should return app metadata."""
        response = await async_client.get("/health/version")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "Nyaya-ZTA"
        assert "version" in data
        assert data["environment"] == "testing"
