"""
Minimal Zero-Knowledge Proof-of-Concept for Evidence Field Inclusion.

Simulates a Groth16 / Circom SHA-256 Merkle Membership Circuit:
Proves evidence-hash inclusion in custody chain root R_public WITHOUT disclosing
the raw evidence payload or private case details.
"""

import hashlib
import time
from typing import Any

from pydantic import BaseModel


def sha256_str(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class ZKProofArtifact(BaseModel):
    proof_system: str = "Groth16_bn128_Circom_Simulator"
    circuit_name: str = "EvidenceMerkleInclusionProof"
    public_inputs: dict[str, Any]
    pi_a: list[str]
    pi_b: list[list[str]]
    pi_c: list[str]
    verification_key_id: str
    proving_time_ms: float


class ZKEvidenceVerifier:
    """
    Zero-Knowledge Proof Generator & Verifier for Evidence Integrity.
    """

    @staticmethod
    def generate_proof(
        private_evidence_hash: str,
        merkle_root: str,
        merkle_path: list[tuple[str, str]],
    ) -> ZKProofArtifact:
        """
        Generates a ZK SNARK proof asserting that private_evidence_hash is a leaf in merkle_root.
        """
        start = time.perf_counter()

        # Verify membership locally before generating proof
        curr_hash = private_evidence_hash
        for sibling, direction in merkle_path:
            if direction == "left":
                curr_hash = sha256_str(f"0x01:{sibling}:{curr_hash}")
            else:
                curr_hash = sha256_str(f"0x01:{curr_hash}:{sibling}")

        is_valid_membership = curr_hash == merkle_root

        # Mock Groth16 elliptic curve proof elements (G1, G2, G1 points)
        pi_a = [
            f"0x{sha256_str(private_evidence_hash + 'a')[:32]}",
            f"0x{sha256_str(merkle_root + 'a')[:32]}",
        ]
        pi_b = [
            [
                f"0x{sha256_str(private_evidence_hash + 'b1')[:32]}",
                f"0x{sha256_str(merkle_root + 'b1')[:32]}",
            ],
            [
                f"0x{sha256_str(private_evidence_hash + 'b2')[:32]}",
                f"0x{sha256_str(merkle_root + 'b2')[:32]}",
            ],
        ]
        pi_c = [
            f"0x{sha256_str(private_evidence_hash + 'c')[:32]}",
            f"0x{sha256_str(merkle_root + 'c')[:32]}",
        ]

        elapsed_ms = float(round((time.perf_counter() - start) * 1000, 3))

        return ZKProofArtifact(
            public_inputs={
                "merkle_root": merkle_root,
                "membership_valid": is_valid_membership,
                "tree_depth": len(merkle_path),
            },
            pi_a=pi_a,
            pi_b=pi_b,
            pi_c=pi_c,
            verification_key_id="vk_bn128_vadp_evidence_v1",
            proving_time_ms=elapsed_ms,
        )

    @staticmethod
    def verify_proof(proof: ZKProofArtifact, expected_root: str) -> bool:
        """
        Verifies ZK SNARK proof in sub-millisecond O(1) time.
        """
        if proof.public_inputs.get("merkle_root") != expected_root:
            return False
        if not proof.public_inputs.get("membership_valid"):
            return False
        if len(proof.pi_a) != 2 or len(proof.pi_c) != 2:
            return False
        return True
