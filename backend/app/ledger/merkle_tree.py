"""
VADP RFC 6962 Binary Merkle Tree Implementation
=====================================================

Binary Merkle Tree for tamper-evident data integrity verification adhering to RFC 6962.
Features:
  - Cryptographic Domain Separation:
      * Leaf Nodes: SHA-256( 0x00 || data )
      * Internal Nodes: SHA-256( 0x01 || left_bytes || right_bytes )
  - Protection against Second-Preimage Attacks
  - Merkle root computation over raw binary digests
  - Merkle inclusion proof generation (O(log N) path)
  - Inclusion proof verification against root
"""

from __future__ import annotations

import hashlib


class MerkleTree:
    """RFC 6962 Binary Merkle Tree builder with cryptographic domain separation."""

    LEAF_PREFIX = b"\x00"
    NODE_PREFIX = b"\x01"

    @staticmethod
    def hash_leaf(data: str | bytes) -> str:
        """
        Calculate RFC 6962 leaf hash: SHA-256(0x00 || data).
        Returns hex string.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha256(MerkleTree.LEAF_PREFIX + data).hexdigest()

    @staticmethod
    def hash_node(left_hex: str, right_hex: str) -> str:
        """
        Calculate RFC 6962 parent node hash: SHA-256(0x01 || left_bytes || right_bytes).
        Accepts hex strings, converts to binary bytes for hashing, returns hex string.
        """
        left_bytes = bytes.fromhex(left_hex)
        right_bytes = bytes.fromhex(right_hex)
        return hashlib.sha256(MerkleTree.NODE_PREFIX + left_bytes + right_bytes).hexdigest()

    @staticmethod
    def hash_data(data: str | bytes) -> str:
        """
        Legacy/General SHA-256 helper (SHA-256 of raw data without domain prefix).
        Maintained for arbitrary data hashing compatibility.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def compute_root(hashes: list[str]) -> str:
        """
        Compute RFC 6962 Merkle Root hash from a list of leaf hashes.
        If empty, returns SHA-256(0x00 || "").
        If odd number of leaves, duplicates last leaf per RFC 6962.
        """
        if not hashes:
            return MerkleTree.hash_leaf("")
        if len(hashes) == 1:
            return hashes[0]

        current_level = list(hashes)

        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            next_level = []
            for i in range(0, len(current_level), 2):
                parent_hash = MerkleTree.hash_node(current_level[i], current_level[i + 1])
                next_level.append(parent_hash)

            current_level = next_level

        return current_level[0]

    @staticmethod
    def generate_proof(hashes: list[str], target_index: int) -> list[dict[str, str]]:
        """
        Generate Merkle inclusion proof path for a leaf at target_index.
        Returns list of dicts: [{"position": "right"|"left", "hash": sibling_hash}]
        """
        if not hashes or target_index < 0 or target_index >= len(hashes):
            return []

        proof = []
        current_level = list(hashes)
        index = target_index

        while len(current_level) > 1:
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            is_right_child = index % 2 == 1
            sibling_index = index - 1 if is_right_child else index + 1

            sibling_hash = current_level[sibling_index]
            position = "left" if is_right_child else "right"
            proof.append({"position": position, "hash": sibling_hash})

            # Build next level
            next_level = []
            for i in range(0, len(current_level), 2):
                next_level.append(MerkleTree.hash_node(current_level[i], current_level[i + 1]))

            current_level = next_level
            index = index // 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: list[dict[str, str]], expected_root: str) -> bool:
        """
        Verify an RFC 6962 Merkle inclusion proof by recalculating the root from the leaf hash and proof path.
        """
        current_hash = leaf_hash

        for node in proof:
            sibling_hash = node["hash"]
            position = node["position"]

            if position == "left":
                current_hash = MerkleTree.hash_node(sibling_hash, current_hash)
            else:
                current_hash = MerkleTree.hash_node(current_hash, sibling_hash)

        return current_hash == expected_root
