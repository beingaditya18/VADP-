"""
IETF SCITT (Supply Chain Integrity, Transparency, and Trust) Statement Profile for VADP.

Media Type: application/vnd.vadp.verification-contract+json
Defines the standard SCITT payload envelope and registration format for
judicial AI decision provenance artifacts.
"""

import json
from typing import Any

from pydantic import BaseModel, Field

SCITT_MEDIA_TYPE = "application/vnd.vadp.verification-contract+json"
SCITT_PROFILE_URI = "https://schema.vadp.org/scitt/v1/verification-contract"


class SCITTProtectedHeader(BaseModel):
    alg: str = Field(default="ES256", description="Signature algorithm (ECDSA NIST P-256)")
    cty: str = Field(default=SCITT_MEDIA_TYPE, description="Content media type")
    kid: str = Field(description="Key ID / Public Key identifier of the PDP issuer")
    profile: str = Field(default=SCITT_PROFILE_URI, description="SCITT statement profile URI")


class SCITTStatementEnvelope(BaseModel):
    protected_header: SCITTProtectedHeader
    payload: dict[str, Any]
    signature: str
    registration_proof: dict[str, Any] | None = None


class VADPScittEncoder:
    """
    Encodes a 7-field VADP Verification Contract into a compliant IETF SCITT Statement.
    """

    @staticmethod
    def encode_contract(
        contract_dict: dict[str, Any], key_id: str, signature: str
    ) -> SCITTStatementEnvelope:
        header = SCITTProtectedHeader(kid=key_id)

        # Ensure canonical JSON payload ordering
        canonical_payload = json.loads(json.dumps(contract_dict, sort_keys=True))

        registration_proof = None
        if contract_dict.get("merkle_proof"):
            registration_proof = {
                "ledger_type": "RFC6962_MerkleTree",
                "leaf_index": contract_dict.get("merkle_leaf_index", 0),
                "root_hash": contract_dict.get("merkle_root_hash"),
                "inclusion_path": contract_dict.get("merkle_proof"),
            }

        return SCITTStatementEnvelope(
            protected_header=header,
            payload=canonical_payload,
            signature=signature,
            registration_proof=registration_proof,
        )

    @staticmethod
    def verify_scitt_statement(statement: SCITTStatementEnvelope) -> bool:
        """Validates SCITT envelope parameters and payload structure."""
        if statement.protected_header.cty != SCITT_MEDIA_TYPE:
            return False
        if not statement.payload.get("contract_hash"):
            return False
        return True
