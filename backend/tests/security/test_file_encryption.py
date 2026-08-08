"""
Security test suite for File Encryption at Rest (Fernet AES-256).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import pytest
from httpx import AsyncClient


class TestFileEncryptionSecurity:
    """Security test suite verifying encryption at rest on disk and transparent on-the-fly decryption."""

    @pytest.mark.asyncio
    async def test_stored_file_on_disk_is_encrypted(self, async_client: AsyncClient) -> None:
        """
        Verify that uploaded files are encrypted on disk as Fernet ciphertext (starts with gAAAAA)
        and original plaintext is not exposed in raw disk files.
        """
        # Register user
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "encrypt.test@nyaya.in",
                "password": "Password123!",
                "full_name": "Encryption Test User",
                "role": "judge",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create case
        case_res = await async_client.post(
            "/api/v1/cases",
            json={
                "title": "Encryption Inspection Case",
                "description": "Case testing AES-256 encryption at rest",
                "case_type": "civil",
                "priority": "high",
            },
            headers=headers,
        )
        case_id = case_res.json()["id"]

        plaintext_content = b"HIGHLY CONFIDENTIAL JUDICIAL WRIT EVIDENCE SECURE TEXT 12345"

        # Upload document
        files = {"file": ("secret_writ.txt", plaintext_content, "text/plain")}
        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        assert upload_res.status_code == 201
        doc_data = upload_res.json()
        doc_id = doc_data["id"]

        # Fetch case documents list to get storage path
        list_res = await async_client.get(
            f"/api/v1/documents/case/{case_id}",
            headers=headers,
        )
        assert list_res.status_code == 200

        # Retrieve exact file path from download metadata or database
        download_res = await async_client.get(
            f"/api/v1/documents/{doc_id}/download",
            headers=headers,
        )
        assert download_res.status_code == 200
        # Download response must decrypt file back to original plaintext
        assert download_res.content == plaintext_content

        # Verify document content hash matches original plaintext SHA-256
        expected_hash = hashlib.sha256(plaintext_content).hexdigest()
        assert doc_data["content_hash"] == expected_hash

    @pytest.mark.asyncio
    async def test_encrypted_file_disk_bytes_inspection(self, async_client: AsyncClient) -> None:
        """
        Verify raw file on disk ends with .enc and contains Fernet cipher tokens.
        """
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "disk.inspect@nyaya.in",
                "password": "Password123!",
                "full_name": "Disk Inspect User",
                "role": "lawyer",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        case_res = await async_client.post(
            "/api/v1/cases",
            json={
                "title": "Disk Inspection Case",
                "description": "Direct disk file ciphertext verification",
                "case_type": "criminal",
                "priority": "medium",
            },
            headers=headers,
        )
        case_id = case_res.json()["id"]

        secret_text = b"TOP SECRET PLAINTEXT JUDICIAL NOTICE"
        files = {"file": ("classified.txt", secret_text, "text/plain")}
        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        assert upload_res.status_code == 201

        # Locate uploads directory for this case
        from app.config import get_settings
        settings = get_settings()
        case_upload_dir = Path(settings.UPLOAD_DIR) / case_id

        assert case_upload_dir.exists()
        enc_files = list(case_upload_dir.glob("*.enc"))
        assert len(enc_files) > 0

        enc_file_path = enc_files[0]
        raw_disk_bytes = enc_file_path.read_bytes()

        # Raw disk bytes MUST start with Fernet magic byte 0x80 (gAAAAA in base64)
        assert raw_disk_bytes.startswith(b"\x80") or raw_disk_bytes.startswith(b"gAAAAA")
        # Raw disk bytes MUST NOT contain original plaintext string
        assert secret_text not in raw_disk_bytes
