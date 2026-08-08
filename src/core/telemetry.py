"""
VADP Telemetry & Prometheus APM Engine
============================================

High-performance APM collector & OpenTelemetry span context tracing manager.

Collects and formats Prometheus standard exposition metrics:
  - http_requests_total{method, endpoint, status}
  - http_request_duration_seconds{method, endpoint}
  - http_requests_in_flight
  - ai_inference_duration_seconds
  - db_query_duration_seconds
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from threading import Lock
from typing import Any, Generator

from app.core.logging import get_logger

logger = get_logger(__name__)


class TelemetryManager:
    """Singleton APM telemetry collector and Prometheus metric exporter."""

    _lock = Lock()
    _in_flight_requests: int = 0
    _request_counters: dict[tuple[str, str, int], int] = defaultdict(int)
    _request_durations: dict[tuple[str, str], list[float]] = defaultdict(list)
    _ai_durations: list[float] = []
    _db_durations: list[float] = []

    @classmethod
    def increment_in_flight(cls) -> None:
        with cls._lock:
            cls._in_flight_requests += 1

    @classmethod
    def decrement_in_flight(cls) -> None:
        with cls._lock:
            cls._in_flight_requests = max(0, cls._in_flight_requests - 1)

    @classmethod
    def record_request(
        cls,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Record an HTTP request completion metric."""
        with cls._lock:
            key_counter = (method.upper(), endpoint, status_code)
            cls._request_counters[key_counter] += 1

            key_duration = (method.upper(), endpoint)
            cls._request_durations[key_duration].append(duration_seconds)
            # Retain last 1000 samples per endpoint for memory efficiency
            if len(cls._request_durations[key_duration]) > 1000:
                cls._request_durations[key_duration].pop(0)

    @classmethod
    def record_ai_inference(cls, duration_seconds: float) -> None:
        """Record AI model inference latency."""
        with cls._lock:
            cls._ai_durations.append(duration_seconds)
            if len(cls._ai_durations) > 500:
                cls._ai_durations.pop(0)

    @classmethod
    def record_db_query(cls, duration_seconds: float) -> None:
        """Record database query execution latency."""
        with cls._lock:
            cls._db_durations.append(duration_seconds)
            if len(cls._db_durations) > 500:
                cls._db_durations.pop(0)

    @classmethod
    @contextmanager
    def trace_span(
        cls, name: str, attributes: dict[str, Any] | None = None
    ) -> Generator[None, None, None]:
        """
        OpenTelemetry style span context manager.
        Tracks execution duration and logs span lifecycle.
        """
        start = time.perf_counter()
        logger.debug(
            f"Span started: {name}",
            extra={"span_name": name, "attributes": attributes or {}},
        )
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            logger.debug(
                f"Span finished: {name}",
                extra={"span_name": name, "duration_ms": round(elapsed * 1000, 2)},
            )

    @classmethod
    def generate_prometheus_text(cls) -> str:
        """Format metrics into standard Prometheus text exposition format (version 0.0.4)."""
        lines: list[str] = [
            "# HELP http_requests_total Total number of HTTP requests processed.",
            "# TYPE http_requests_total counter",
        ]

        with cls._lock:
            # 1. HTTP Request Counters
            for (method, endpoint, status), count in cls._request_counters.items():
                lines.append(
                    f'http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}'
                )

            lines.extend(
                [
                    "# HELP http_requests_in_flight Current number of HTTP requests being processed.",
                    "# TYPE http_requests_in_flight gauge",
                    f"http_requests_in_flight {cls._in_flight_requests}",
                ]
            )

            # 2. HTTP Request Durations (Histograms / Summaries)
            lines.extend(
                [
                    "# HELP http_request_duration_seconds HTTP request latency in seconds.",
                    "# TYPE http_request_duration_seconds summary",
                ]
            )
            for (method, endpoint), durations in cls._request_durations.items():
                if durations:
                    total_sum = sum(durations)
                    count = len(durations)
                    lines.append(
                        f'http_request_duration_seconds_sum{{method="{method}",endpoint="{endpoint}"}} {total_sum:.6f}'
                    )
                    lines.append(
                        f'http_request_duration_seconds_count{{method="{method}",endpoint="{endpoint}"}} {count}'
                    )

            # 3. AI Inference Metrics
            lines.extend(
                [
                    "# HELP ai_inference_duration_seconds AI model inference latency in seconds.",
                    "# TYPE ai_inference_duration_seconds summary",
                ]
            )
            if cls._ai_durations:
                lines.append(
                    f"ai_inference_duration_seconds_sum {sum(cls._ai_durations):.6f}"
                )
                lines.append(
                    f"ai_inference_duration_seconds_count {len(cls._ai_durations)}"
                )
            else:
                lines.append("ai_inference_duration_seconds_sum 0.0")
                lines.append("ai_inference_duration_seconds_count 0")

            # 4. DB Query Metrics
            lines.extend(
                [
                    "# HELP db_query_duration_seconds Database query duration in seconds.",
                    "# TYPE db_query_duration_seconds summary",
                ]
            )
            if cls._db_durations:
                lines.append(
                    f"db_query_duration_seconds_sum {sum(cls._db_durations):.6f}"
                )
                lines.append(
                    f"db_query_duration_seconds_count {len(cls._db_durations)}"
                )
            else:
                lines.append("db_query_duration_seconds_sum 0.0")
                lines.append("db_query_duration_seconds_count 0")

        lines.append("")  # Trailing newline required by Prometheus spec
        return "\n".join(lines)

    @classmethod
    def clear(cls) -> None:
        """Reset internal metrics (useful for test suites)."""
        with cls._lock:
            cls._in_flight_requests = 0
            cls._request_counters.clear()
            cls._request_durations.clear()
            cls._ai_durations.clear()
            cls._db_durations.clear()
