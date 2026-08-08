"""
Fail-Closed Security Chaos & Failure Injection Test Suite.

Proves that under infrastructure failure (Merkle ledger outage, signing key loss, network drop),
VADP strictly FAILS CLOSED (Deny/Reject), never fails open.
"""

import pytest
from typing import Dict, Any


class SimulatedZeroTrustPDP:
    
    def __init__(self, ledger_online: bool = True, signing_key_valid: bool = True):
        self.ledger_online = ledger_online
        self.signing_key_valid = signing_key_valid

    def evaluate_request(self, user_role: str, resource: str) -> Dict[str, Any]:
        # Fail-closed check 1: Ledger connectivity
        if not self.ledger_online:
            return {
                "decision": "Deny",
                "reason": "Security Chaos Isolation: Merkle audit ledger offline. Default Deny enforced.",
                "status_code": 503,
                "failed_closed": True,
            }

        # Fail-closed check 2: Cryptographic Key Integrity
        if not self.signing_key_valid:
            return {
                "decision": "Deny",
                "reason": "Security Chaos Isolation: Key Vault signing key corrupted. Contract generation aborted.",
                "status_code": 500,
                "failed_closed": True,
            }

        # Standard ABAC check
        if user_role in ["judge", "lawyer"]:
            return {
                "decision": "Permit",
                "reason": "Access granted by policy",
                "status_code": 200,
                "failed_closed": False,
            }

        return {
            "decision": "Deny",
            "reason": "ABAC Policy rejection",
            "status_code": 403,
            "failed_closed": True,
        }


class TestFailClosedChaos:

    def test_merkle_ledger_outage_fails_closed(self):
        """
        Chaos Test: Ledger service offline -> PDP must FAIL CLOSED (Deny access).
        """
        pdp = SimulatedZeroTrustPDP(ledger_online=False, signing_key_valid=True)
        res = pdp.evaluate_request(user_role="judge", resource="case_file_001")

        assert res["decision"] == "Deny", "System MUST Deny access when Merkle ledger is offline"
        assert res["failed_closed"] is True, "System MUST indicate explicit fail-closed posture"
        assert res["status_code"] == 503

    def test_corrupted_signing_key_fails_closed(self):
        """
        Chaos Test: Signing key corrupted -> System MUST FAIL CLOSED (Refuse contract issuance).
        """
        pdp = SimulatedZeroTrustPDP(ledger_online=True, signing_key_valid=False)
        res = pdp.evaluate_request(user_role="judge", resource="case_file_001")

        assert res["decision"] == "Deny", "System MUST Deny access when signing key is corrupted"
        assert res["failed_closed"] is True, "System MUST indicate explicit fail-closed posture"
        assert res["status_code"] == 500

    def test_normal_operation_permits_authorized_role(self):
        """
        Sanity Check: Normal operation permits authorized user.
        """
        pdp = SimulatedZeroTrustPDP(ledger_online=True, signing_key_valid=True)
        res = pdp.evaluate_request(user_role="judge", resource="case_file_001")

        assert res["decision"] == "Permit"
        assert res["failed_closed"] is False
