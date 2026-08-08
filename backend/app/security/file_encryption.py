"""
VADP File Encryption at Rest
==================================

AES-256 Symmetric encryption using Fernet for local document storage security.
Ensures document files on disk are unreadable ciphertext while providing
transparent decryption for authorized API downloads.
"""

from __future__ import annotations

import base64
import hashlib
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileEncryption:
    """Fernet AES-256 file encryption engine."""

    _fernet_instance: Fernet | None = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get or initialize cached Fernet cipher instance."""
        if cls._fernet_instance is None:
            settings = get_settings()
            raw_key = settings.FILE_ENCRYPTION_KEY

            if raw_key and len(raw_key.strip()) > 0:
                key_bytes = raw_key.encode("utf-8")
            else:
                # Deterministically derive 32-byte URL-safe base64 Fernet key from JWT_SECRET_KEY
                digest = hashlib.sha256(settings.JWT_SECRET_KEY.encode("utf-8")).digest()
                key_bytes = base64.urlsafe_b64encode(digest)

            cls._fernet_instance = Fernet(key_bytes)
        return cls._fernet_instance

    @classmethod
    def encrypt_file(cls, file_path: str | Path) -> Path:
        """
        Encrypt file in-place or into .enc file and delete original plaintext.

        Returns:
            Path to encrypted ciphertext file on disk.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File to encrypt not found: {path}")

        fernet = cls._get_fernet()

        with open(path, "rb") as f:
            plaintext = f.read()

        ciphertext = fernet.encrypt(plaintext)

        # Output encrypted file with .enc extension if not already present
        if path.suffix == ".enc":
            enc_path = path
        else:
            enc_path = path.with_suffix(path.suffix + ".enc")

        with open(enc_path, "wb") as f:
            f.write(ciphertext)

        # Unlink plaintext file if output path differs
        if path != enc_path and path.exists():
            path.unlink()

        logger.info("File encrypted at rest", extra={"plaintext": str(path), "ciphertext": str(enc_path)})
        return enc_path

    @classmethod
    def decrypt_file(cls, encrypted_path: str | Path) -> bytes:
        """
        Decrypt file and return original plaintext bytes.
        """
        path = Path(encrypted_path)
        if not path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {path}")

        fernet = cls._get_fernet()

        with open(path, "rb") as f:
            ciphertext = f.read()

        return fernet.decrypt(ciphertext)

    @classmethod
    def decrypt_to_temp_file(cls, encrypted_path: str | Path, original_filename: str) -> Path:
        """
        Decrypt encrypted file into a temporary file for download streaming.

        Returns:
            Path to temporary decrypted file.
        """
        plaintext = cls.decrypt_file(encrypted_path)
        ext = Path(original_filename).suffix or ".bin"

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(plaintext)
        temp_file.close()

        return Path(temp_file.name)
