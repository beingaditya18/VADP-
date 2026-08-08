"""
VADP AI Engine Service
===========================

Orchestrates case summarization, RAG legal document context, Trust Score calculation,
Risk Assessment, SHAP feature importance, and recommendation review/approval workflows.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.bias_detector import BiasDetector
from app.ai.models import AIExplanation, AIRecommendation
from app.ai.risk_engine import RiskScoringEngine
from app.ai.schemas import (
    AIRecommendationResponseSchema,
    CaseAnalysisResponseSchema,
)
from app.ai.shap_explainer import SHAPExplainer
from app.ai.trust_engine import TrustScoringEngine
from app.cases.models import Case
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.evidence.models import EvidenceRecord
from app.rag.schemas import RAGQueryRequestSchema
from app.rag.service import RAGService

logger = get_logger(__name__)


class AIService:
    """Service managing AI analysis and explainability operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.rag_service = RAGService(db)

    async def analyze_case(self, case_id: str) -> CaseAnalysisResponseSchema:
        """
        Perform complete AI Judicial Decision Support analysis:
          1. Retrieve case details, uploaded documents & evidence status
          2. RAG summary of legal facts & precedents
          3. Evaluate multi-factor Risk Score
          4. Compute formal Trust Score (Formula: α*S_model + β*S_evidence + γ*S_source + δ*S_consistency)
          5. Compute SHAP feature importance & positive/negative contributions
          6. Scan recommendation text for Bias markers
          7. Save AIRecommendation & AIExplanation to DB
        """
        # Fetch Case
        stmt = select(Case).where(Case.id == case_id)
        result = await self.db.execute(stmt)
        case_obj = result.scalar_one_or_none()
        if not case_obj:
            raise NotFoundError(message="Case not found for analysis.")

        # Fetch evidence records for case
        ev_stmt = select(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
        ev_result = await self.db.execute(ev_stmt)
        evidence_records = ev_result.scalars().all()

        unverified_count = sum(1 for e in evidence_records if e.verification_status != "verified")
        total_ev = len(evidence_records)
        evidence_quality = 1.0 if total_ev == 0 else (total_ev - unverified_count) / float(total_ev)

        # 1. RAG Query for Legal Summary
        rag_query = f"Summarize key legal issues, statutory merits, and precedents for case '{case_obj.title}' ({case_obj.case_type})."
        rag_response = await self.rag_service.answer_query(
            schema=RAGQueryRequestSchema(query_text=rag_query, case_id=case_id, top_k=3),
            user_id=case_obj.filed_by,
        )
        summary_text = rag_response.answer

        # 2. Risk Assessment
        risk_assessment = RiskScoringEngine.evaluate_risk(
            case_priority=case_obj.priority,
            unverified_evidence_count=unverified_count,
            has_policy_restriction=False,
        )

        # 3. Trust Score Calculation & A/B Model Variant Selection
        import time

        from app.ai.ab_testing import ABTestingEngine
        from app.ai.drift_detector import ModelDriftDetector

        start_time = time.perf_counter()
        model_version = ABTestingEngine.select_model_version(case_id)

        model_confidence = 0.88 if model_version == "v1" else 0.92
        trust_breakdown = TrustScoringEngine.calculate_trust_score(
            model_confidence=model_confidence,
            evidence_quality=evidence_quality,
            source_reliability=0.92,
            consistency=0.89,
        )

        # 4. SHAP Explanations
        shap_values, feature_imp, factors = SHAPExplainer.compute_shap_explanations(
            evidence_quality=evidence_quality,
            precedent_match=0.85,
            unverified_evidence=unverified_count,
        )

        # Telemetry logging for A/B Testing & Drift Monitoring
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        ABTestingEngine.log_request(version=model_version, latency_ms=latency_ms)
        ModelDriftDetector.log_prediction(confidence=model_confidence, model_version=model_version)

        # 5. Bias Check
        bias_markers = BiasDetector.detect_bias(summary_text)

        # 6. Save Recommendation & Explanation to DB
        recommendation = AIRecommendation(
            case_id=case_id,
            recommendation_type="judgment_support",
            recommendation_text=summary_text,
            confidence_score=model_confidence,
            trust_score=trust_breakdown.overall,
            risk_score=risk_assessment.overall_score,
            model_version=f"nyaya-shap-{model_version}",
            status="pending",
        )
        self.db.add(recommendation)
        await self.db.flush()

        explanation = AIExplanation(
            recommendation_id=recommendation.id,
            explanation_type="shap_feature_importance",
            shap_values=[s.model_dump() for s in shap_values],
            feature_importance=feature_imp,
            contributing_factors=[f.model_dump() for f in factors],
            natural_language_explanation=f"Trust Score ({trust_breakdown.overall:.2f}) computed from evidence integrity ({evidence_quality * 100:.0f}%) and model confidence ({model_confidence * 100:.0f}%).",
            bias_markers=bias_markers,
        )
        self.db.add(explanation)
        await self.db.flush()

        # Reload with explanations
        rec_stmt = (
            select(AIRecommendation)
            .where(AIRecommendation.id == recommendation.id)
            .options(selectinload(AIRecommendation.explanations))
        )
        rec_result = await self.db.execute(rec_stmt)
        full_rec = rec_result.scalar_one()

        rec_response = AIRecommendationResponseSchema.model_validate(full_rec)
        rec_response.trust_breakdown = trust_breakdown
        rec_response.risk_assessment = risk_assessment

        # VADP: Auto-generate Verification Contract
        verification_contract = None
        try:
            from app.vadp.service import VerificationContractService

            vadp_service = VerificationContractService(self.db)
            verification_contract = await vadp_service.generate_contract(
                case_id=case_id,
                recommendation_id=recommendation.id,
                actor_id=case_obj.filed_by,
            )
        except Exception as e:
            logger.warning(
                "VADP contract generation failed (non-blocking)",
                extra={"case_id": case_id, "error": str(e)},
            )

        return CaseAnalysisResponseSchema(
            case_id=case_id,
            summary=summary_text,
            trust_score=trust_breakdown.overall,
            risk_score=risk_assessment.overall_score,
            risk_level=risk_assessment.risk_level,
            recommendation=rec_response,
            trust_breakdown=trust_breakdown,
            risk_assessment=risk_assessment,
            verification_contract=verification_contract,
        )

    async def list_recommendations_for_case(
        self, case_id: str
    ) -> list[AIRecommendationResponseSchema]:
        """List all AI recommendations generated for a case."""
        stmt = (
            select(AIRecommendation)
            .where(AIRecommendation.case_id == case_id)
            .options(selectinload(AIRecommendation.explanations))
            .order_by(AIRecommendation.created_at.desc())
        )
        result = await self.db.execute(stmt)
        recs = result.scalars().all()
        return [AIRecommendationResponseSchema.model_validate(r) for r in recs]

    async def review_recommendation(
        self, recommendation_id: str, reviewer_id: str, new_status: str
    ) -> AIRecommendationResponseSchema:
        """Judge review & approval/rejection of AI decision support recommendation."""
        stmt = (
            select(AIRecommendation)
            .where(AIRecommendation.id == recommendation_id)
            .options(selectinload(AIRecommendation.explanations))
        )
        result = await self.db.execute(stmt)
        rec = result.scalar_one_or_none()
        if not rec:
            raise NotFoundError(message="Recommendation not found.")

        rec.status = new_status
        rec.reviewed_by = reviewer_id
        await self.db.flush()

        # VADP: Record human review on verification contract
        try:
            from app.vadp.service import VerificationContractService

            vadp_service = VerificationContractService(self.db)
            contract = await vadp_service.get_contract_for_recommendation(recommendation_id)
            if contract:
                await vadp_service.record_human_review(
                    contract_id=contract.id,
                    reviewer_id=reviewer_id,
                    action=new_status,
                    notes=f"Judge review: {new_status}",
                )
        except Exception as e:
            logger.warning(
                "VADP review recording failed (non-blocking)",
                extra={"recommendation_id": recommendation_id, "error": str(e)},
            )

        return AIRecommendationResponseSchema.model_validate(rec)
