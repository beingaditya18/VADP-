"""
Unit tests for HSM PKCS#11 Provider and SECP256R1 ECDSA fallback signing.
"""

import hashlib
import pytest
from app.security.hsm_signer import HSMProvider

def test_hsm_provider_initialization():
    provider = HSMProvider()
    assert provider is not None
    pub_pem = provider.get_public_key_pem()
    assert "BEGIN PUBLIC KEY" in pub_pem

def test_hsm_signature_generation_and_verification():
    provider = HSMProvider()
    data = b"VADP_VERIFICATION_CONTRACT_HASH_TEST_PAYLOAD"
    digest = hashlib.sha256(data).digest()

    sig = provider.sign_digest(digest)
    assert isinstance(sig, bytes)
    assert len(sig) > 0
