"""
Unit & API Integration tests for Tamper-Evident Audit Ledger.
Tests:
  - Merkle Tree Root Computation & Inclusion Proof verification
  - SHA-256 Block Hash chaining logic
  - ECDSA Digital Signatures (key generation, signing, verifying)
  - Full Audit Ledger API (recording entries, sealing blocks, verifying chain integrity)
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.ledger.hash_chain import HashChain
from app.ledger.merkle_tree import MerkleTree
from app.ledger.signatures import LedgerSigner


class TestMerkleTree:
    """Unit tests for Merkle Tree computation."""

    def test_merkle_root_single_leaf(self) -> None:
        h1 = MerkleTree.hash_data("leaf1")
        root = MerkleTree.compute_root([h1])
        assert root == h1

    def test_merkle_root_multiple_leaves(self) -> None:
        h1 = MerkleTree.hash_data("leaf1")
        h2 = MerkleTree.hash_data("leaf2")
        h3 = MerkleTree.hash_data("leaf3")

        root = MerkleTree.compute_root([h1, h2, h3])
        assert len(root) == 64  # SHA-256 hex string

    def test_merkle_proof_generation_and_verification(self) -> None:
        h1 = MerkleTree.hash_data("data1")
        h2 = MerkleTree.hash_data("data2")
        h3 = MerkleTree.hash_data("data3")
        h4 = MerkleTree.hash_data("data4")
        leaves = [h1, h2, h3, h4]

        root = MerkleTree.compute_root(leaves)

        # Generate proof for leaf 2 (index 1: h2)
        proof = MerkleTree.generate_proof(leaves, target_index=1)
        assert len(proof) > 0

        # Verify proof
        is_valid = MerkleTree.verify_proof(h2, proof, root)
        assert is_valid is True

        # Verify with wrong leaf hash fails
        invalid_leaf = MerkleTree.hash_data("tampered_data")
        assert MerkleTree.verify_proof(invalid_leaf, proof, root) is False


class TestECDSASignatures:
    """Unit tests for ECDSA digital signatures."""

    def test_sign_and_verify(self) -> None:
        signer = LedgerSigner()
        block_hash = HashChain.calculate_block_hash(
            block_index=1,
            timestamp_str="2026-07-21T10:00:00Z",
            previous_hash="0" * 64,
            data_hash="abc" * 20,
            merkle_root="def" * 20,
        )

        signature = signer.sign_block(block_hash)
        assert len(signature) > 0

        assert signer.verify_signature(block_hash, signature) is True
        assert signer.verify_signature("tampered_block_hash", signature) is False


class TestLedgerAPI:
    """API Integration tests for /api/v1/ledger."""

    @pytest.mark.asyncio
    async def test_ledger_record_seal_and_verify_flow(self, async_client: AsyncClient) -> None:
        # 1. Register Admin User
        admin_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "audit.officer@nyaya.gov.in",
                "password": "AdminPassword123!",
                "full_name": "Audit Officer",
                "role": "admin",
            },
        )
        token = admin_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Record 2 audit entries
        entry1_res = await async_client.post(
            "/api/v1/ledger/entries",
            json={
                "entry_type": "case_access",
                "action": "Accessed Case NYA-CIV-2026-0001",
                "resource_type": "case",
                "resource_id": "case-uuid-1",
            },
            headers=headers,
        )
        assert entry1_res.status_code == 201
        entry1_id = entry1_res.json()["id"]

        entry2_res = await async_client.post(
            "/api/v1/ledger/entries",
            json={
                "entry_type": "policy_change",
                "action": "Updated ABAC owner condition",
                "resource_type": "policy",
            },
            headers=headers,
        )
        assert entry2_res.status_code == 201

        # 3. Seal block manually
        seal_res = await async_client.post("/api/v1/ledger/blocks/seal", headers=headers)
        assert seal_res.status_code == 200
        block_data = seal_res.json()
        assert block_data["block_index"] == 0
        assert block_data["entries_count"] == 2
        assert block_data["signature"] is not None

        # 4. Generate Merkle Inclusion Proof for entry 1
        proof_res = await async_client.get(f"/api/v1/ledger/entries/{entry1_id}/proof", headers=headers)
        assert proof_res.status_code == 200
        proof_data = proof_res.json()
        assert proof_data["is_valid"] is True
        assert proof_data["merkle_root"] == block_data["merkle_root"]

        # 5. Verify full chain integrity
        verify_res = await async_client.get("/api/v1/ledger/verify", headers=headers)
        assert verify_res.status_code == 200
        verify_data = verify_res.json()
        assert verify_data["is_valid"] is True, f"Chain verification failed: {verify_data['details']}"
        assert verify_data["verified_blocks"] == 1
        assert "Zero tampering detected" in verify_data["details"]
