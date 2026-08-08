"""
VADP Locust Load Testing Workload Suite
=============================================

Simulates multi-role concurrent users performing authentication, case browsing,
telemetry polling, document uploading, and explainable AI analysis requests.

Usage:
  locust -f backend/tests/load/locustfile.py --host http://localhost:8000
"""

from __future__ import annotations

import random
import uuid

try:
    from locust import HttpUser, between, task
    HAS_LOCUST = True
except ImportError:
    HAS_LOCUST = False
    # Mock classes if locust is not installed
    class HttpUser:  # type: ignore
        pass
    def task(weight=1):
        def decorator(f):
            return f
        return decorator
    def between(a, b):
        return None


class NyayaUser(HttpUser):
    """Simulated concurrent user performing weighted judicial workflow requests."""

    wait_time = between(0.1, 1.0) if HAS_LOCUST else None  # Fast throughput burst simulation

    def on_start(self):
        """Register and authenticate user session upon spawn."""
        if not hasattr(self, "client") or self.client is None:
            return

        self.user_email = f"loadtest_{uuid.uuid4().hex[:8]}@nyaya.in"
        self.password = "Password123!"

        # Register user
        reg_resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.user_email,
                "password": self.password,
                "full_name": "Load Test Citizen",
                "role": "citizen",
            },
        )
        if reg_resp.status_code in (200, 201):
            data = reg_resp.json()
            self.token = data.get("access_token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task(10)
    def list_cases(self):
        """Fetch list of cases (High frequency read)."""
        self.client.get("/api/v1/cases", headers=getattr(self, "headers", {}))

    @task(5)
    def check_health_and_metrics(self):
        """Poll telemetry metrics & detailed readiness probes."""
        self.client.get("/health/detailed")
        self.client.get("/metrics")

    @task(3)
    def create_and_view_case(self):
        """Create case and inspect case record."""
        resp = self.client.post(
            "/api/v1/cases",
            json={
                "title": f"Load Test Case {random.randint(1000, 9999)}",
                "description": "Property dispute case created during load testing",
                "case_type": "civil",
                "priority": "medium",
            },
            headers=getattr(self, "headers", {}),
        )
        if resp.status_code in (200, 201):
            case_id = resp.json().get("id")
            if case_id:
                self.client.get(f"/api/v1/cases/{case_id}", headers=getattr(self, "headers", {}))

    @task(1)
    def upload_document(self):
        """Upload test document attachment."""
        # Create case first
        c_resp = self.client.post(
            "/api/v1/cases",
            json={
                "title": "Document Attachment Case",
                "description": "Attachment testing under load",
                "case_type": "civil",
            },
            headers=getattr(self, "headers", {}),
        )
        if c_resp.status_code in (200, 201):
            case_id = c_resp.json()["id"]
            files = {"file": ("doc_sample.txt", b"Sample legal text for load test", "text/plain")}
            self.client.post(f"/api/v1/documents/upload/{case_id}", files=files, headers=getattr(self, "headers", {}))
