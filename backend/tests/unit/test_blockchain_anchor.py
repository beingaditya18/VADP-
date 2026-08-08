"""
VADP Blockchain Evidence Anchoring & BSA 2023 §63(4) Unit Tests
"""

import pytest
from app.evidence.blockchain_anchor import (
    BlockchainAnchorEngine,
    BlockchainTransactionReceipt,
    BSACertificate63,
)


class TestBlockchainAnchorEngine:
    """Test suite for Blockchain Anchoring and BSA 2023 §63(4) Certificates."""

    def test_blockchain_transaction_anchoring(self):
        """Test anchoring an evidence hash to a smart contract transaction receipt."""
        evidence_id = "ev_case_101_01"
        integrity_hash = "a" * 64

        receipt = BlockchainAnchorEngine.anchor_to_blockchain(
            evidence_id=evidence_id,
            integrity_hash=integrity_hash,
        )

        assert isinstance(receipt, BlockchainTransactionReceipt)
        assert receipt.tx_hash.startswith("0x")
        assert len(receipt.tx_hash) == 66
        assert receipt.block_number > 0
        assert receipt.status == "SUCCESS"

    def test_bsa_63_certificate_generation_and_verification(self):
        """Test generation and cryptographic signature verification of BSA 2023 §63(4) certificates."""
        cert = BlockchainAnchorEngine.generate_bsa_certificate(
            case_id="case_2026_99",
            evidence_id="ev_doc_99",
            document_id="doc_99",
            evidence_type="forensic_pdf",
            integrity_hash="b" * 64,
        )

        assert isinstance(cert, BSACertificate63)
        assert cert.certificate_id.startswith("BSA63-CERT-")
        assert cert.is_legally_admissible is True
        assert cert.statute_reference == "Bharatiya Sakshya Adhiniyam (BSA), 2023 — Section 63(4)"

        # Verify NIST P-256 ECDSA signature
        is_valid = BlockchainAnchorEngine.verify_bsa_certificate(cert)
        assert is_valid is True

    def test_bsa_certificate_tampered_signature_rejection(self):
        """Verify that an altered signature in a BSA certificate is rejected."""
        cert = BlockchainAnchorEngine.generate_bsa_certificate(
            case_id="case_2026_99",
            evidence_id="ev_doc_99",
            document_id="doc_99",
            evidence_type="forensic_pdf",
            integrity_hash="b" * 64,
        )

        # Alter hash inside certificate payload
        cert.content_hash_sha256 = "c" * 64

        is_valid = BlockchainAnchorEngine.verify_bsa_certificate(cert)
        assert is_valid is False
