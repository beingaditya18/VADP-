"""
VADP Digital Signatures Module (ECDSA P-256 & Ed25519)
======================================================

Asymmetric cryptography using NIST P-256 (SECP256R1) curve backed by HSM Key Management,
and Ed25519 (EdDSA over Curve25519) for standard-model security reduction.
Used for digital signature signing of finalized audit ledger blocks and VADP contracts.
"""

from __future__ import annotations

import base64
import logging

from app.ledger.ed25519_signatures import Ed25519LedgerSigner

logger = logging.getLogger(__name__)


class LedgerSigner:
    """Digital Signer supporting both ECDSA NIST P-256 and Ed25519 standard-model signatures."""

    def __init__(self, algorithm: str = "ed25519", private_key_path: str | None = None) -> None:
        self.algorithm = algorithm.lower()
        if self.algorithm == "ed25519":
            self._ed25519_signer = Ed25519LedgerSigner()
        else:
            try:
                from app.security.hsm import HSMKeyManager

                self._hsm_provider = HSMKeyManager.get_provider()
            except Exception:
                from app.security.hsm_signer import default_hsm_provider

                self._hsm_provider = default_hsm_provider

    def sign_block(self, block_hash: str) -> str:
        """
        Sign a block hash string using configured key manager (Ed25519 or ECDSA P-256).
        Returns Base64 signature string.
        """
        if self.algorithm == "ed25519":
            return self._ed25519_signer.sign_message(block_hash.encode("utf-8"))

        sig_bytes = self._hsm_provider.sign_digest(block_hash.encode("utf-8"))
        return base64.b64encode(sig_bytes).decode("utf-8")

    def verify_signature(
        self, block_hash: str, signature_b64: str, public_key_pem: str | None = None
    ) -> bool:
        """
        Verify signature against block_hash.
        """
        if self.algorithm == "ed25519":
            return self._ed25519_signer.verify_signature(
                block_hash.encode("utf-8"), signature_b64, public_key_pem
            )

        # ECDSA verification fallback
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec

            sig_bytes = base64.b64decode(signature_b64.encode("utf-8"))
            if public_key_pem:
                pub_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
            else:
                pem_str = self._hsm_provider.get_public_key_pem()
                pub_key = serialization.load_pem_public_key(pem_str.encode("utf-8"))

            assert isinstance(pub_key, ec.EllipticCurvePublicKey)
            pub_key.verify(sig_bytes, block_hash.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False
