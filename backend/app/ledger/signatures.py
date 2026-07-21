"""
Nyaya-ZTA ECDSA Digital Signatures Module
=========================================

Asymmetric cryptography using NIST P-256 (SECP256R1) curve.
Used for digital signature signing of finalized audit ledger blocks and verification.
"""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LedgerSigner:
    """ECDSA Digital Signer for Ledger Block verification."""

    def __init__(self, private_key_path: str | None = None) -> None:
        settings = get_settings()
        key_path = Path(private_key_path or settings.LEDGER_SIGNING_KEY_PATH)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        if not key_path.exists():
            self._private_key = self._generate_and_save_key(key_path)
        else:
            self._private_key = self._load_key(key_path)

        self._public_key = self._private_key.public_key()

    def _generate_and_save_key(self, path: Path) -> ec.EllipticCurvePrivateKey:
        """Generate new ECDSA SECP256R1 keypair and write to PEM file."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        path.write_bytes(pem)
        logger.info("Generated new ECDSA ledger signing key", extra={"path": str(path)})
        return private_key

    def _load_key(self, path: Path) -> ec.EllipticCurvePrivateKey:
        """Load private key from PEM file."""
        pem_bytes = path.read_bytes()
        return serialization.load_pem_private_key(pem_bytes, password=None)  # type: ignore

    def sign_block(self, block_hash: str) -> str:
        """
        Sign a block hash string using private key. Returns Base64 signature string.
        """
        signature = self._private_key.sign(
            block_hash.encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        return base64.b64encode(signature).decode("utf-8")

    def verify_signature(self, block_hash: str, signature_b64: str) -> bool:
        """
        Verify signature against block_hash using public key.
        """
        try:
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(
                signature,
                block_hash.encode("utf-8"),
                ec.ECDSA(hashes.SHA256()),
            )
            return True
        except (InvalidSignature, Exception):
            return False
