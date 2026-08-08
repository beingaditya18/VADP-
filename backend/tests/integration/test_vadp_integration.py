"""
VADP VADP End-to-End Integration Test
============================================

Full end-to-end integration test validating:
  1. Case creation → Recommendation generation → Auto-VADP Contract generation
  2. Independent contract verification
  3. Human review recording & contract completeness re-evaluation
  4. Contract finalization
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models import AIRecommendation
from app.cases.models import Case
from app.vadp.service import VerificationContractService


@pytest.mark.asyncio
async def test_full_vadp_contract_lifecycle(db_session: AsyncSession):
    """
    Test the entire VADP lifecycle:
      - Create case & AI recommendation
      - Generate Verification Contract
      - Perform independent verification
      - Submit judge human review
      - Finalize contract
    """
    from app.auth.models import User

    # 0. Create dummy user
    user = User(
        id="test-user-1",
        email="testuser1@example.com",
        full_name="Test User 1",
        role="citizen",
        hashed_password="test-hash",
    )
    judge = User(
        id="judge-user-1",
        email="judge1@example.com",
        full_name="Judge User 1",
        role="judge",
        hashed_password="test-hash",
    )
    db_session.add(user)
    db_session.add(judge)
    await db_session.flush()

    # 1. Create dummy case
    case = Case(
        id="vadp-test-case-1",
        case_number="VADP-2026-001",
        title="VADP Verification Lifecycle Test",
        case_type="civil",
        filed_by="test-user-1",
        filing_date=datetime.now(timezone.utc).date(),
    )
    db_session.add(case)
    await db_session.flush()

    # 2. Create dummy recommendation
    rec = AIRecommendation(
        id="vadp-test-rec-1",
        case_id="vadp-test-case-1",
        recommendation_type="judgment_assistance",
        recommendation_text="Grant petition based on evidence integrity.",
        confidence_score=0.92,
        trust_score=0.88,
        risk_score=0.12,
        status="pending",
        metadata_={
            "trust_breakdown": {
                "overall": 0.88,
                "model_confidence": 0.90,
                "evidence_quality": 0.85,
                "source_reliability": 0.88,
                "consistency": 0.89,
            },
            "risk_features": [],
        },
    )
    db_session.add(rec)
    await db_session.commit()

    # 3. Generate Verification Contract
    vadp_service = VerificationContractService(db_session)
    contract_res = await vadp_service.generate_contract(
        case_id="vadp-test-case-1",
        recommendation_id="vadp-test-rec-1",
        actor_id="test-user-1",
    )

    assert contract_res.case_id == "vadp-test-case-1"
    assert contract_res.recommendation_id == "vadp-test-rec-1"
    assert contract_res.contract_hash is not None
    assert len(contract_res.contract_hash) == 64
    assert contract_res.digital_signature is not None
    assert contract_res.events is not None

    # 4. Independent Verification
    verification_res = await vadp_service.verify_contract(contract_res.id)
    assert verification_res.hash_valid is True
    assert verification_res.signature_valid is True

    # 5. Judge Human Review
    reviewed_contract = await vadp_service.record_human_review(
        contract_id=contract_res.id,
        reviewer_id="judge-user-1",
        action="approved",
        notes="Reviewed all evidence and SHAP values.",
    )

    assert reviewed_contract.human_review.status == "approved"
    assert reviewed_contract.human_review.reviewed_by == "judge-user-1"

    # 6. Finalize Contract
    finalized_contract = await vadp_service.finalize_contract(contract_res.id)
    assert finalized_contract.finalized_at is not None
