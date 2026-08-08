"""
Unit tests for Ed25519 (EdDSA over Curve25519) Digital Signatures
"""

import pytest
from app.ledger.ed25519_signatures import Ed25519LedgerSigner
from app.ledger.signatures import LedgerSigner


def test_ed25519_signer_standalone():
    signer = Ed25519LedgerSigner()
    msg = b"VADP_VERIFIABLE_AUDIT_BLOCK_HASH_2026"
    sig_b64 = signer.sign_message(msg)
    
    assert sig_b64 is not None
    assert len(sig_b64) > 0
    assert signer.verify_signature(msg, sig_b64) is True
    assert signer.verify_signature(b"TAMPERED_MSG", sig_b64) is False


def test_ledger_signer_ed25519_integration():
    signer = LedgerSigner(algorithm="ed25519")
    block_hash = "0x8f2d5e6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e"
    sig = signer.sign_block(block_hash)
    
    assert sig is not None
    assert signer.verify_signature(block_hash, sig) is True
    assert signer.verify_signature("0x0000000000000000000000000000000000000000000000000000000000000000", sig) is False
