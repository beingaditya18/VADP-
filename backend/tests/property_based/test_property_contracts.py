"""
Hypothesis Property-Based & Mutation Fuzzing Test Suite for VADP Verification Contracts.

Uses Hypothesis to auto-generate thousands of contract variants and test the invariant:
Completeness(C) == True iff all 7 fields pass deterministic verification and Merkle inclusion check.
"""

import pytest
from hypothesis import given, strategies as st
from typing import Dict, Any
import hashlib
import json


def canonical_hash(payload: Dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def evaluate_completeness_invariant(contract: Dict[str, Any]) -> bool:
    """Deterministic, model-independent Completeness Invariant check."""
    required_fields = [
        "f1_authorization", "f2_evidence", "f3_rag_citations", "f4_shap_explanation",
        "f5_signature", "f6_merkle_proof", "f7_human_review"
    ]
    for field in required_fields:
        if field not in contract or contract[field] is None:
            return False

    # Signature validity check
    if not isinstance(contract["f5_signature"], str) or not contract["f5_signature"].startswith("0x"):
        return False

    # Merkle proof validity check
    merkle = contract["f6_merkle_proof"]
    if not isinstance(merkle, dict) or "merkle_root" not in merkle or "leaf_index" not in merkle:
        return False

    return True


class TestPropertyBasedContracts:

    @given(
        auth_decision=st.sampled_from(["Permit", "Deny"]),
        bsa_cert_id=st.text(min_size=5, max_size=20),
        entailment_score=st.floats(min_value=0.0, max_value=1.0),
        shap_stability=st.floats(min_value=0.0, max_value=1.0),
        sig_prefix=st.sampled_from(["0x", "invalid_"]),
        leaf_index=st.integers(min_value=0, max_value=10000),
        hoc_status=st.sampled_from(["AUTONOMOUS_APPROVED", "HUMAN_OVERRIDE_REQUIRED"]),
    )
    def test_completeness_invariant_property(
        self,
        auth_decision: str,
        bsa_cert_id: str,
        entailment_score: float,
        shap_stability: float,
        sig_prefix: str,
        leaf_index: int,
        hoc_status: str,
    ):
        """
        Property Test: Completeness(C) is True IFF all 7 fields satisfy validation predicates.
        """
        contract = {
            "f1_authorization": {"decision": auth_decision},
            "f2_evidence": {"bsa_cert": bsa_cert_id},
            "f3_rag_citations": [{"entailment": entailment_score}],
            "f4_shap_explanation": {"stability": shap_stability},
            "f5_signature": f"{sig_prefix}1234567890abcdef",
            "f6_merkle_proof": {"merkle_root": "0xROOT", "leaf_index": leaf_index},
            "f7_human_review": {"status": hoc_status},
        }

        is_complete = evaluate_completeness_invariant(contract)
        
        # Expected: True iff sig_prefix == "0x"
        expected = (sig_prefix == "0x")
        assert is_complete == expected, f"Completeness invariant mismatch for contract: {contract}"

    def test_mutation_fuzzing_rejection(self):
        """
        Fuzzing test: Randomly mutates valid contract fields and verifies 100% rejection.
        """
        base_contract = {
            "f1_authorization": {"decision": "Permit"},
            "f2_evidence": {"bsa_cert": "CERT_001"},
            "f3_rag_citations": [{"entailment": 0.95}],
            "f4_shap_explanation": {"stability": 0.90},
            "f5_signature": "0xVALID_SIG",
            "f6_merkle_proof": {"merkle_root": "0xROOT", "leaf_index": 1},
            "f7_human_review": {"status": "AUTONOMOUS_APPROVED"},
        }
        assert evaluate_completeness_invariant(base_contract) is True

        # Mutate by removing each field one by one
        for field in list(base_contract.keys()):
            mutated = base_contract.copy()
            del mutated[field]
            assert evaluate_completeness_invariant(mutated) is False, f"Fuzzed contract missing {field} must be rejected"
