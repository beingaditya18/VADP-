"""
VADP VADP Adversarial Security Test Suite
================================================

Validates VADP cryptographic tamper-resistance and security invariants:
  1. Contract payload tampering detection (SHA-256 hash mismatch)
  2. Signature forgery & corruption resistance (NIST P-256 ECDSA)
  3. Merkle inclusion proof tampering detection (RFC 6962 leaf mismatch)
  4. Decision Provenance Timeline hash chain breaking detection
  5. Completeness invariant enforcement & missing component flagging
"""

from __future__ import annotations

import copy
import hashlib
import pytest
from datetime import datetime, timezone

from app.ai.models import AIRecommendation
from app.auth.models import User
from app.cases.models import Case
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import get_session_factory
from app.ledger.merkle_tree import MerkleTree
from app.ledger.signatures import LedgerSigner
from app.vadp.completeness import CompletenessChecker
from app.vadp.contract_hasher import ContractHasher
from app.vadp.models import ContractEvent, VerificationContract
from app.vadp.repository import VerificationContractRepository
from app.vadp.service import VerificationContractService


async def create_single_valid_contract(db) -> VerificationContract:
    """Helper fixture to create one signed valid contract in DB."""
    import uuid
    repo = VerificationContractRepository(db)

    user_email = f"sec_{uuid.uuid4().hex[:8]}@nyaya.gov.in"
    user_id = str(uuid.uuid4())
    test_user = User(
        id=user_id,
        email=user_email,
        hashed_password=hash_password("Password123!"),
        full_name="Security Auditor",
        role="judge",
        is_active=True,
    )
    db.add(test_user)

    case_id = str(uuid.uuid4())
    c_obj = Case(
        id=case_id,
        case_number=f"INSC-SEC-{uuid.uuid4().hex[:8]}",
        title="Supreme Court Security Audit Case",
        case_type="Constitutional",
        status="under_review",
        priority="high",
        filed_by=user_id,
    )
    db.add(c_obj)
    await db.flush()

    rec_id = str(uuid.uuid4())
    rec_obj = AIRecommendation(
        id=rec_id,
        case_id=case_id,
        recommendation_type="judgment_support",
        recommendation_text="Security test recommendation.",
        confidence_score=0.95,
        trust_score=0.90,
        risk_score=0.10,
        status="approved",
    )
    db.add(rec_obj)
    await db.flush()

    signer = LedgerSigner()
    now = datetime.now(timezone.utc)

    ev_list = [{
        "evidence_id": "ev_sec_1",
        "integrity_hash": "a" * 64,
        "verification_status": "verified",
        "document_id": "doc_sec_1",
        "evidence_type": "judicial_judgment",
        "file_name": "sec_doc.pdf",
    }]
    rag_list = [{
        "chunk_id": "chunk_sec_1",
        "document_id": "doc_sec_1",
        "similarity_score": 0.95,
        "snippet": "Grounded legal snippet for security test.",
    }]
    rag_meta = {"embedding_model": "all-MiniLM-L6-v2", "top_k": 5}
    shap_vals = [{"feature_name": "Constitutional Precedent", "attribution_value": 0.45}]
    feat_imp = {"Constitutional Precedent": 0.45}
    contrib_fac = [{"feature_name": "Constitutional Precedent", "attribution_value": 0.45}]
    trust_bd = {
        "overall": 0.90,
        "model_confidence": 0.92,
        "evidence_quality": 0.94,
        "source_reliability": 0.90,
        "consistency": 0.88,
        "weights": {"alpha": 0.35, "beta": 0.35, "gamma": 0.15, "delta": 0.15},
    }

    hashable = ContractHasher.build_hashable_contract_data(
        contract_version="1.0.0",
        case_id=case_id,
        recommendation_id=rec_id,
        authorization_result="allow",
        authorization_reason="Authorized bench judge role",
        evidence_hashes=ev_list,
        rag_citations=rag_list,
        rag_retrieval_metadata=rag_meta,
        shap_values=shap_vals,
        feature_importance=feat_imp,
        contributing_factors=contrib_fac,
        trust_score=0.90,
        trust_breakdown=trust_bd,
        risk_score=0.10,
        risk_level="low",
        risk_features=[],
        generated_at=now,
    )

    c_hash = ContractHasher.compute_contract_hash(hashable)
    sig = signer.sign_block(c_hash)
    merkle_leaf = MerkleTree.hash_leaf(c_hash)

    vc = VerificationContract(
        id=str(uuid.uuid4()),
        case_id=case_id,
        recommendation_id=rec_id,
        contract_version="1.0.0",
        authorization_result="allow",
        authorization_reason="Authorized bench judge role",
        evidence_hashes=ev_list,
        evidence_count=1,
        evidence_verified=1,
        rag_citations=rag_list,
        rag_retrieval_metadata=rag_meta,
        shap_values=shap_vals,
        feature_importance=feat_imp,
        contributing_factors=contrib_fac,
        trust_score=0.90,
        trust_breakdown=trust_bd,
        risk_score=0.10,
        risk_level="low",
        human_review_status="approved",
        review_action="approved",
        contract_hash=c_hash,
        digital_signature=sig,
        signing_algorithm="ECDSA-P256-SHA256",
        merkle_leaf_hash=merkle_leaf,
        merkle_proof=[{"position": "left", "hash": c_hash[:32]}],
        completeness_status="complete",
        completeness_checks={"has_authorization": True, "has_evidence": True},
        generated_at=now,
    )
    db.add(vc)
    await db.commit()
    return vc


@pytest.mark.asyncio
async def test_contract_tampering_detection():
    """Adversarial test: Tampering with any payload field triggers SHA-256 hash mismatch."""
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as db:
        vc = await create_single_valid_contract(db)
        service = VerificationContractService(db)

        # Baseline: valid verification
        v0 = await service.verify_contract(vc.id)
        assert v0.is_valid is True
        assert v0.hash_valid is True

        # Tamper 1: Alter evidence hash
        vc.evidence_hashes[0]["integrity_hash"] = "b" * 64
        await db.flush()
        v1 = await service.verify_contract(vc.id)
        assert v1.hash_valid is False
        assert v1.is_valid is False
        assert any("HASH MISMATCH" in f for f in v1.failures)

        # Revert
        vc.evidence_hashes[0]["integrity_hash"] = "a" * 64
        await db.flush()

        # Tamper 2: Alter trust score
        vc.trust_score = 0.10
        await db.flush()
        v2 = await service.verify_contract(vc.id)
        assert v2.hash_valid is False
        assert v2.is_valid is False


@pytest.mark.asyncio
async def test_signature_forgery_resistance():
    """Adversarial test: Forged or corrupted ECDSA signatures fail verification."""
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as db:
        vc = await create_single_valid_contract(db)
        service = VerificationContractService(db)

        # Baseline
        v0 = await service.verify_contract(vc.id)
        assert v0.signature_valid is True

        # Forged signature
        vc.digital_signature = "MEQCID...FORGED_ECDSA_SIGNATURE...=="
        await db.flush()
        v1 = await service.verify_contract(vc.id)
        assert v1.signature_valid is False
        assert v1.is_valid is False
        assert any("SIGNATURE INVALID" in f for f in v1.failures)


@pytest.mark.asyncio
async def test_merkle_inclusion_tampering():
    """Adversarial test: Corrupting Merkle leaf hash breaks Merkle verification."""
    await init_db()
    session_factory = get_session_factory()

    async with session_factory() as db:
        vc = await create_single_valid_contract(db)
        service = VerificationContractService(db)

        # Baseline
        v0 = await service.verify_contract(vc.id)
        assert v0.merkle_valid is True

        # Corrupt Merkle leaf hash
        vc.merkle_leaf_hash = "f" * 64
        await db.flush()
        v1 = await service.verify_contract(vc.id)
        assert v1.merkle_valid is False
        assert v1.is_valid is False
        assert any("MERKLE MISMATCH" in f for f in v1.failures)


@pytest.mark.asyncio
async def test_provenance_timeline_hash_chain_break():
    """Adversarial test: Modifying a past timeline event breaks parent hash chain."""
    evt1_hash = ContractHasher.compute_chained_event_hash({"step": 1}, parent_hash=None)
    evt2_hash = ContractHasher.compute_chained_event_hash({"step": 2}, parent_hash=evt1_hash)

    # Tamper with step 1 payload
    tampered_evt1_hash = ContractHasher.compute_chained_event_hash({"step": 1, "tampered": True}, parent_hash=None)

    # Verification of step 2 against tampered step 1 hash fails
    recomputed_evt2_hash = ContractHasher.compute_chained_event_hash({"step": 2}, parent_hash=tampered_evt1_hash)
    assert recomputed_evt2_hash != evt2_hash


@pytest.mark.asyncio
async def test_completeness_invariant_enforcement():
    """Adversarial test: Incomplete contract missing criteria is flagged as incomplete."""
    inv = CompletenessChecker.evaluate(
        authorization_result="allow",
        evidence_count=0,  # Missing evidence!
        rag_citations_count=5,
        shap_values_count=4,
        trust_score=0.90,
        risk_score=0.10,
        digital_signature="valid_sig",
        merkle_leaf_hash="valid_leaf",
        human_review_status="approved",
    )

    assert inv.overall_complete is False
    assert "evidence" in inv.missing_components
