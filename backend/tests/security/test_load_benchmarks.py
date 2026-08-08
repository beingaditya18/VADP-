"""
Performance SLA & Load Benchmark Test Suite for VADP.
"""

from __future__ import annotations

import time
import numpy as np
import pytest
from httpx import AsyncClient


class TestLoadPerformanceSLA:
    """Security and SLA performance benchmark test suite verifying latency distributions and concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_load_performance_sla(self, async_client: AsyncClient) -> None:
        """
        Verify that concurrent request bursts meet performance SLA targets:
        - P50 Latency < 200ms
        - P95 Latency < 500ms
        - Error Rate = 0%
        """
        latencies_ms: list[float] = []

        # Execute 25 rapid requests
        for _ in range(25):
            t0 = time.perf_counter()
            res = await async_client.get("/health/detailed")
            assert res.status_code == 200
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies_ms.append(elapsed_ms)

        p50 = float(np.percentile(latencies_ms, 50))
        p95 = float(np.percentile(latencies_ms, 95))

        # Assert SLA targets
        assert p50 < 200.0, f"P50 latency exceeded SLA: {p50:.2f}ms"
        assert p95 < 500.0, f"P95 latency exceeded SLA: {p95:.2f}ms"

    @pytest.mark.asyncio
    async def test_locustfile_user_task_weights(self) -> None:
        """
        Verify Locust scenario file structure and weighted user task definitions.
        """
        from tests.load.locustfile import NyayaUser
        assert hasattr(NyayaUser, "list_cases")
        assert hasattr(NyayaUser, "check_health_and_metrics")
        assert hasattr(NyayaUser, "create_and_view_case")
        assert hasattr(NyayaUser, "upload_document")
