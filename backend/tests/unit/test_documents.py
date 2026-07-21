"""
Unit & API Integration tests for Document Storage & Hash Verification.
"""

from __future__ import annotations

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDocumentsAPI:
    """Test suite for /api/v1/documents endpoints."""

    async def test_document_upload_and_download(self, async_client: AsyncClient) -> None:
        # 1. Register User & File Case
        user_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "lawyer.verma@nyaya.in",
                "password": "Password123!",
                "full_name": "Advocate Verma",
                "role": "lawyer",
                "bar_number": "MAH/4567/2021",
            },
        )
        token = user_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        case_res = await async_client.post(
            "/api/v1/cases",
            json={
                "title": "Commercial Dispute Contract Claim",
                "case_type": "Commercial",
            },
            headers=headers,
        )
        case_id = case_res.json()["id"]

        # 2. Upload sample document file
        file_content = b"Sample legal petition text content for SHA-256 integrity test."
        files = {"file": ("petition_affidavit.txt", io.BytesIO(file_content), "text/plain")}

        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        assert upload_res.status_code == 201
        doc_data = upload_res.json()
        assert doc_data["file_name"] == "petition_affidavit.txt"
        assert "content_hash" in doc_data
        assert len(doc_data["content_hash"]) == 64  # SHA-256 hex string length

        doc_id = doc_data["id"]

        # 3. Download document back
        download_res = await async_client.get(
            f"/api/v1/documents/{doc_id}/download",
            headers=headers,
        )
        assert download_res.status_code == 200
        assert download_res.content == file_content
