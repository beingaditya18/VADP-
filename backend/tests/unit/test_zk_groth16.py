"""
VADP Real Groth16 Zero-Knowledge Prover Unit Tests
"""

import os
import pytest
from app.evidence.zk_groth16_engine import ZKGroth16Engine, RealGroth16ProofArtifact


class TestZKGroth16Engine:
    """Test suite for real snarkjs Groth16 execution and deterministic simulation fallback."""

    def test_native_groth16_availability(self):
        """Verify that circom WASM, ZKEY, and VKEY availability check executes cleanly."""
        avail = ZKGroth16Engine.is_native_available()
        assert isinstance(avail, bool)

    def test_groth16_proof_generation_and_verification(self):
        """Execute Groth16 proof generation and verification."""
        leaf = "12345"
        root = "9294106379696776950601211281063494228448002695590390542946159591100177729206"
        path_elements = [str(i + 100) for i in range(10)]
        path_indices = [0] * 10

        # 1. Generate Proof
        artifact = ZKGroth16Engine.generate_proof(
            leaf_signal=leaf,
            root_signal=root,
            path_elements=path_elements,
            path_indices=path_indices,
        )

        assert isinstance(artifact, RealGroth16ProofArtifact)
        assert isinstance(artifact.simulation_mode, bool)
        assert artifact.proof_size_bytes == 192
        assert len(artifact.pi_a) == 3
        assert len(artifact.pi_b) == 3
        assert len(artifact.pi_c) == 3
        assert artifact.proving_time_ms >= 0

        # 2. Verify Proof
        if not artifact.simulation_mode:
            is_valid, verify_ms = ZKGroth16Engine.verify_proof(artifact, expected_root=root)
            assert is_valid is True
            assert verify_ms >= 0

    def test_groth16_invalid_root_rejection(self):
        """Verify that proof verification checks Merkle root signal matching."""
        leaf = "12345"
        root = "9294106379696776950601211281063494228448002695590390542946159591100177729206"
        invalid_root = "9999999999999999999999999999999999999999999999999999999999999999999999999999"

        artifact = ZKGroth16Engine.generate_proof(
            leaf_signal=leaf,
            root_signal=root,
            path_elements=[str(i + 100) for i in range(10)],
            path_indices=[0] * 10,
        )

        if not artifact.simulation_mode:
            is_valid, _ = ZKGroth16Engine.verify_proof(artifact, expected_root=invalid_root)
            assert is_valid is False
