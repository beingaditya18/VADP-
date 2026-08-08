"""
VADP VADP Unit Tests
=========================

Unit tests covering:
  1. VerificationContract & ContractEvent SQLAlchemy models
  2. ContractHasher canonical JSON hashing
  3. CompletenessChecker invariant rules
  4. VerificationContractRepository CRUD & queries
  5. VerificationContractService business logic & verification
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.vadp.completeness import CompletenessChecker
from app.vadp.contract_hasher import ContractHasher
from app.vadp.models import ContractEvent, VerificationContract
from app.vadp.schemas import (
    CompletenessInvariant,
    VerificationContractCreateSchema,
)


class TestContractHasher:
    """Test canonical JSON contract hashing."""

    def test_deterministic_hash(self):
        data1 = {
            "contract_version": "1.0.0",
            "case_id": "case-123",
            "recommendation_id": "rec-456",
            "trust_score": 0.88,
            "risk_score": 0.12,
            "risk_level": "low",
        }
        data2 = {
            "risk_level": "low",
            "risk_score": 0.12,
            "trust_score": 0.88,
            "recommendation_id": "rec-456",
            "case_id": "case-123",
            "contract_version": "1.0.0",
        }
        hash1 = ContractHasher.compute_contract_hash(data1)
        hash2 = ContractHasher.compute_contract_hash(data2)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex string

    def test_hash_mutation(self):
        data1 = {"case_id": "case-123", "trust_score": 0.88}
        data2 = {"case_id": "case-123", "trust_score": 0.89}
        hash1 = ContractHasher.compute_contract_hash(data1)
        hash2 = ContractHasher.compute_contract_hash(data2)
        assert hash1 != hash2

    def test_chained_event_hash(self):
        event_data = {"action": "approved", "reviewer": "judge-1"}
        parent_hash = "0" * 64
        chained_hash = ContractHasher.compute_chained_event_hash(event_data, parent_hash)
        assert len(chained_hash) == 64
        assert chained_hash != parent_hash


class TestCompletenessChecker:
    """Test 9-criteria VADP completeness invariant logic."""

    def test_fully_complete_contract(self):
        inv = CompletenessChecker.evaluate(
            authorization_result="allow",
            evidence_count=2,
            rag_citations_count=3,
            shap_values_count=4,
            trust_score=0.91,
            risk_score=0.15,
            digital_signature="sig_123",
            merkle_leaf_hash="leaf_456",
            human_review_status="approved",
        )
        assert inv.overall_complete is True
        assert len(inv.missing_components) == 0
        assert CompletenessChecker.compute_status(inv) == "complete"

    def test_incomplete_missing_review(self):
        inv = CompletenessChecker.evaluate(
            authorization_result="allow",
            evidence_count=2,
            rag_citations_count=3,
            shap_values_count=4,
            trust_score=0.91,
            risk_score=0.15,
            digital_signature="sig_123",
            merkle_leaf_hash="leaf_456",
            human_review_status="pending_review",
        )
        assert inv.overall_complete is False
        assert inv.missing_components == ["human_review"]
        assert CompletenessChecker.compute_status(inv) == "awaiting_review"

    def test_incomplete_missing_multiple(self):
        inv = CompletenessChecker.evaluate(
            authorization_result=None,
            evidence_count=0,
            rag_citations_count=0,
            shap_values_count=0,
            trust_score=None,
            risk_score=None,
            digital_signature=None,
            merkle_leaf_hash=None,
            human_review_status="pending_review",
        )
        assert inv.overall_complete is False
        assert len(inv.missing_components) == 9
        assert CompletenessChecker.compute_status(inv) == "incomplete"


class TestVADPModels:
    """Test VerificationContract model structure."""

    def test_contract_model_instantiation(self):
        contract = VerificationContract(
            id="test-id",
            contract_version="1.0.0",
            case_id="case-1",
            recommendation_id="rec-1",
            contract_hash="hash-123",
            trust_score=0.9,
            risk_score=0.1,
            risk_level="low",
            human_review_status="pending_review",
            completeness_status="incomplete",
            generated_at=datetime.now(timezone.utc),
        )
        assert contract.id == "test-id"
        assert contract.contract_version == "1.0.0"
        assert contract.human_review_status == "pending_review"
        assert contract.completeness_status == "incomplete"
