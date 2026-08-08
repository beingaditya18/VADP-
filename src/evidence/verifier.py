"""
VADP Evidence Hash Verifier
================================

Core cryptographic verification logic.
Recomputes SHA-256 of physical file on disk and compares against recorded integrity hash.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import aiofiles

from app.evidence.schemas import EvidenceVerificationResultSchema


class EvidenceVerifier:
    """Cryptographic file integrity verifier."""

    @staticmethod
    async def verify_file_integrity(file_path: str, expected_hash: str) -> EvidenceVerificationResultSchema:
        """
        Stream local file from disk, calculate SHA-256, and compare with expected hash.
        """
        now = datetime.now(timezone.utc)
        sha256_hash = hashlib.sha256()

        try:
            if file_path.endswith(".enc"):
                from app.security.file_encryption import FileEncryption
                plaintext = FileEncryption.decrypt_file(file_path)
                sha256_hash.update(plaintext)
            else:
                async with aiofiles.open(file_path, "rb") as f:
                    while chunk := await f.read(64 * 1024):
                        sha256_hash.update(chunk)
            computed_hash = sha256_hash.hexdigest()
        except Exception as e:
            return EvidenceVerificationResultSchema(
                is_valid=False,
                status="tampered",
                expected_hash=expected_hash,
                computed_hash="ERROR_READING_FILE",
                verification_time=now,
                message=f"Failed to read evidence file on disk: {str(e)}",
            )

        is_valid = (computed_hash == expected_hash)
        status_str = "verified" if is_valid else "tampered"
        message_str = (
            "Integrity verified successfully: Hash matches recorded evidence state."
            if is_valid
            else "TAMPERING DETECTED: File content hash does NOT match recorded evidence state!"
        )

        return EvidenceVerificationResultSchema(
            is_valid=is_valid,
            status=status_str,
            expected_hash=expected_hash,
            computed_hash=computed_hash,
            verification_time=now,
            message=message_str,
        )
