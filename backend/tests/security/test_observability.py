"""
Security & APM Observability test suite for VADP.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from app.core.telemetry import TelemetryManager


@pytest.fixture(autouse=True)
def clear_telemetry():
    TelemetryManager.clear()
    yield
    TelemetryManager.clear()


class TestObservabilityAPM:
    """Security and observability test suite for APM metrics, detailed health checks, and correlation headers."""

    @pytest.mark.asyncio
    async def test_prometheus_metrics_endpoint(self, async_client: AsyncClient) -> None:
        """
        Verify that GET /metrics returns standard Prometheus text exposition format.
        """
        # Make request to record metrics
        await async_client.get("/api/v1/auth/me")

        res = await async_client.get("/metrics")
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]

        body = res.text
        assert "http_requests_total" in body
        assert "http_request_duration_seconds" in body
        assert "http_requests_in_flight" in body

    @pytest.mark.asyncio
    async def test_detailed_health_check_endpoint(self, async_client: AsyncClient) -> None:
        """
        Verify that GET /health/detailed returns detailed subsystem connectivity statuses.
        """
        res = await async_client.get("/health/detailed")
        assert res.status_code == 200
        data = res.json()

        assert "status" in data
        assert "subsystems" in data
        assert "database" in data["subsystems"]
        assert data["subsystems"]["database"] == "healthy"
        assert "faiss_index" in data["subsystems"]
        assert "rate_limiter" in data["subsystems"]

    @pytest.mark.asyncio
    async def test_correlation_request_id_propagation(self, async_client: AsyncClient) -> None:
        """
        Verify X-Request-ID propagation for end-to-end tracing correlation.
        """
        custom_id = "test-correlation-trace-12345"
        res = await async_client.get(
            "/api/v1/auth/me",
            headers={"X-Request-ID": custom_id},
        )
        assert res.headers.get("x-request-id") == custom_id
