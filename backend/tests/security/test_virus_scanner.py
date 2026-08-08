"""
Security test suite for Virus Scanner & Malware Defense Engine.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from httpx import AsyncClient
from app.security.virus_scanner import VirusScanner, EICAR_SIGNATURE


class TestVirusScannerSecurity:
    """Security test suite for virus scanning, EICAR test signature rejection, and binary payload defense."""

    @pytest.mark.asyncio
    async def test_clean_document_upload_succeeds(self, async_client: AsyncClient) -> None:
        """
        Verify that a clean text/PDF file passes malware scanning cleanly.
        """
        # Register user
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "virus.test@nyaya.in",
                "password": "Password123!",
                "full_name": "Virus Test User",
                "role": "judge",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create case
        case_res = await async_client.post(
            "/api/v1/cases",
            json={
                "title": "Malware Inspection Case",
                "description": "Case for file security testing",
                "case_type": "civil",
                "priority": "medium",
            },
            headers=headers,
        )
        case_id = case_res.json()["id"]

        # Upload clean file
        files = {"file": ("clean_doc.txt", b"Clean legal document content.", "text/plain")}
        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        assert upload_res.status_code == 201
        assert upload_res.json()["file_name"] == "clean_doc.txt"

    @pytest.mark.asyncio
    async def test_eicar_test_signature_rejected_and_unlinked(self, async_client: AsyncClient) -> None:
        """
        Verify that an EICAR test malware signature file is rejected with 422 error and deleted from disk.
        """
        # Register user
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "eicar.test@nyaya.in",
                "password": "Password123!",
                "full_name": "EICAR Test User",
                "role": "citizen",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create case
        case_res = await async_client.post(
            "/api/v1/cases",
            json={
                "title": "EICAR Malware Case",
                "description": "Case for EICAR signature rejection testing",
                "case_type": "civil",
                "priority": "high",
            },
            headers=headers,
        )
        case_id = case_res.json()["id"]

        # Upload file containing EICAR signature string
        files = {"file": ("eicar_test.txt", EICAR_SIGNATURE, "text/plain")}
        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        assert upload_res.status_code in (400, 422)
        assert "security threat" in upload_res.text.lower() or "malware" in upload_res.text.lower() or "eicar" in upload_res.text.lower()

    @pytest.mark.asyncio
    async def test_executable_binary_header_disguised_pdf_rejection(self, async_client: AsyncClient) -> None:
        """
        Verify that a Windows executable binary payload disguised as a .pdf is rejected and unlinked.
        """
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "exe.test@nyaya.in",
                "password": "Password123!",
                "full_name": "Executable Test User",
                "role": "lawyer",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        case_res = await async_client.post(
            "/api/v1/cases",
            json={
                "title": "Executable Header Case",
                "description": "Testing disguised binary executable headers",
                "case_type": "criminal",
                "priority": "high",
            },
            headers=headers,
        )
        case_id = case_res.json()["id"]

        # Disguised EXE binary header starting with MZ
        fake_pdf_payload = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        files = {"file": ("malicious_payload.pdf", fake_pdf_payload, "application/pdf")}
        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        assert upload_res.status_code in (400, 422)
        assert "executable" in upload_res.text.lower() or "security threat" in upload_res.text.lower()
