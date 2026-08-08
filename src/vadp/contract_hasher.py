"""
VADP VADP Contract Hasher
==============================

Canonical JSON hashing utility for Verification Contract integrity.

The contract hash is computed by:
  1. Extracting all provenance fields into a deterministic dictionary
  2. Serializing to canonical JSON (sorted keys, no whitespace, UTF-8)
  3. Computing SHA-256 of the canonical JSON bytes

This ensures that the same contract data always produces the same hash,
regardless of field ordering or serialization differences.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


class ContractHasher:
    """Deterministic canonical JSON hashing for Verification Contracts."""

    @staticmethod
    def compute_contract_hash(contract_data: dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of canonical JSON representation.

        The input dict should contain all provenance-relevant fields
        of the Verification Contract. The hash covers:
          - Authorization provenance
          - Evidence hashes
          - RAG citations and metadata
          - SHAP values and feature importance
          - Trust score and breakdown
          - Risk score, level, and features
          - Recommendation ID and case ID
          - Contract version

        Fields that change after creation (human_review, merkle_proof,
        finalized_at) are NOT included in the hash to allow contract
        evolution without invalidation.
        """
        canonical = ContractHasher._to_canonical_json(contract_data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_event_hash(event_data: dict[str, Any]) -> str:
        """
        Compute SHA-256 hash of a contract event's data payload.

        Used for building the internal hash chain within a contract's
        Decision Provenance Timeline.
        """
        canonical = ContractHasher._to_canonical_json(event_data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_chained_event_hash(
        event_data: dict[str, Any],
        parent_hash: str | None,
    ) -> str:
        """
        Compute hash for a contract event chained to its predecessor.

        Hash = SHA-256( parent_hash || event_data_hash )

        If parent_hash is None (genesis event), uses empty string.
        """
        event_hash = ContractHasher.compute_event_hash(event_data)
        chain_input = (parent_hash or "") + event_hash
        return hashlib.sha256(chain_input.encode("utf-8")).hexdigest()

    @staticmethod
    def build_hashable_contract_data(
        contract_version: str,
        case_id: str,
        recommendation_id: str,
        authorization_result: str,
        authorization_reason: str | None,
        evidence_hashes: list[dict[str, Any]],
        rag_citations: list[dict[str, Any]],
        rag_retrieval_metadata: dict[str, Any],
        shap_values: list[dict[str, Any]],
        feature_importance: dict[str, Any],
        contributing_factors: list[dict[str, Any]],
        trust_score: float,
        trust_breakdown: dict[str, Any],
        risk_score: float,
        risk_level: str,
        risk_features: list[dict[str, Any]],
        generated_at: datetime,
    ) -> dict[str, Any]:
        """
        Build the deterministic dictionary used for contract hash computation.

        Only provenance-immutable fields are included. Mutable fields
        (human_review_status, merkle_proof, finalized_at) are excluded
        so the hash remains stable across the contract lifecycle.
        """
        if isinstance(generated_at, datetime):
            if generated_at.tzinfo is None:
                from datetime import timezone

                generated_at = generated_at.replace(tzinfo=timezone.utc)
            gen_str = generated_at.isoformat()
        else:
            gen_str = str(generated_at)

        return {
            "contract_version": contract_version,
            "case_id": case_id,
            "recommendation_id": recommendation_id,
            "authorization_result": authorization_result,
            "authorization_reason": authorization_reason or "",
            "evidence_hashes": evidence_hashes,
            "rag_citations": rag_citations,
            "rag_retrieval_metadata": rag_retrieval_metadata,
            "shap_values": shap_values,
            "feature_importance": feature_importance,
            "contributing_factors": contributing_factors,
            "trust_score": round(trust_score, 6),
            "trust_breakdown": trust_breakdown,
            "risk_score": round(risk_score, 6),
            "risk_level": risk_level,
            "risk_features": risk_features,
            "generated_at": gen_str,
        }

    @staticmethod
    def _to_canonical_json(data: dict[str, Any]) -> str:
        """
        Serialize a dictionary to canonical JSON.

        Rules:
          - Keys sorted alphabetically (recursive)
          - No whitespace padding
          - UTF-8 encoding
          - ensure_ascii=False for proper Unicode handling
          - datetime objects converted to ISO 8601 strings
        """
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=ContractHasher._json_serializer,
        )

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for types not handled by default."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
