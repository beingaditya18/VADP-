"""
Unit & API Integration tests for Evidence Registration & Cryptographic Verification.
"""

from __future__ import annotations

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestEvidenceAPI:
    """Test suite for /api/v1/evidence endpoints."""

    async def test_evidence_registration_and_hash_verification(self, async_client: AsyncClient) -> None:
        # 1. Register User, Case & Upload File
        user_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "forensic.expert@nyaya.in",
                "password": "Password123!",
                "full_name": "Dr. R. Forensic",
                "role": "admin",
            },
        )
        token = user_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        case_res = await async_client.post(
            "/api/v1/cases",
            json={"title": "Cybercrime Digital Audit Case", "case_type": "Cybercrime"},
            headers=headers,
        )
        case_id = case_res.json()["id"]

        file_content = b"Digital Forensic Audit Log Artifact 2026-07-21"
        files = {"file": ("forensic_log.txt", io.BytesIO(file_content), "text/plain")}

        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        doc_id = upload_res.json()["id"]
        original_hash = upload_res.json()["content_hash"]

        # 2. Register Evidence
        evidence_res = await async_client.post(
            "/api/v1/evidence",
            json={
                "document_id": doc_id,
                "case_id": case_id,
                "evidence_type": "digital_forensic",
            },
            headers=headers,
        )
        assert evidence_res.status_code == 201
        evidence_data = evidence_res.json()
        assert evidence_data["integrity_hash"] == original_hash
        assert evidence_data["verification_status"] == "pending"

        evidence_id = evidence_data["id"]

        # 3. Verify Evidence Integrity
        verify_res = await async_client.post(
            f"/api/v1/evidence/{evidence_id}/verify",
            headers=headers,
        )
        assert verify_res.status_code == 200
        verify_data = verify_res.json()
        assert verify_data["is_valid"] is True
        assert verify_data["status"] == "verified"
        assert verify_data["computed_hash"] == original_hash
