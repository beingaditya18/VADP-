"""
Unit & Integration tests for AI Engine, Trust Formula, Risk Assessment, SHAP Explainer, and AI REST API.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.ai.bias_detector import BiasDetector
from app.ai.risk_engine import RiskScoringEngine
from app.ai.shap_explainer import SHAPExplainer
from app.ai.trust_engine import TrustScoringEngine


class TestTrustEngine:
    """Unit tests for formal Trust Formula."""

    def test_trust_calculation_bounded(self) -> None:
        result = TrustScoringEngine.calculate_trust_score(
            model_confidence=0.90,
            evidence_quality=1.0,
            source_reliability=0.95,
            consistency=0.90,
        )
        assert 0.0 <= result.overall <= 1.0
        assert result.overall >= 0.90
        assert result.weights["alpha"] == 0.35
        assert result.weights["beta"] == 0.35


class TestRiskEngine:
    """Unit tests for Multi-factor Risk Engine."""

    def test_risk_evaluation_high_priority(self) -> None:
        risk = RiskScoringEngine.evaluate_risk(
            case_priority="high",
            unverified_evidence_count=2,
            has_policy_restriction=False,
        )
        assert risk.overall_score > 0.40
        assert risk.risk_level in ["high", "critical", "medium"]

    def test_risk_evaluation_low_priority(self) -> None:
        risk = RiskScoringEngine.evaluate_risk(
            case_priority="low",
            unverified_evidence_count=0,
            has_policy_restriction=False,
        )
        assert risk.overall_score < 0.35
        assert risk.risk_level == "low"


class TestSHAPExplainer:
    """Unit tests for SHAP feature importance calculation."""

    def test_shap_values(self) -> None:
        shap_values, importance, factors = SHAPExplainer.compute_shap_explanations(
            evidence_quality=1.0,
            precedent_match=0.85,
            unverified_evidence=0,
        )
        assert len(shap_values) == 4
        assert len(factors) == 4
        assert importance["Evidence Cryptographic Integrity"] > 0


class TestBiasDetector:
    """Unit tests for Bias Detection."""

    def test_clean_text_no_bias(self) -> None:
        flags = BiasDetector.detect_bias("Property dispute analysis based on statutory notice requirements.")
        assert len(flags) == 0

    def test_biased_text_flagged(self) -> None:
        flags = BiasDetector.detect_bias("Dispute resolution considering socio-economic class of respondent.")
        assert len(flags) > 0


@pytest.mark.asyncio
class TestAIAPI:
    """API Integration tests for /api/v1/ai."""

    async def test_analyze_case_flow(self, async_client: AsyncClient) -> None:
        # 1. Register User & File Case
        user_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "judge.verma@nyaya.gov.in",
                "password": "Password123!",
                "full_name": "Justice Verma",
                "role": "judge",
            },
        )
        token = user_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        case_res = await async_client.post(
            "/api/v1/cases",
            json={"title": "High Court Appeal Property Right", "case_type": "Civil", "priority": "high"},
            headers=headers,
        )
        case_id = case_res.json()["id"]

        # 2. Trigger Full AI Analysis
        analyze_res = await async_client.post(f"/api/v1/ai/cases/{case_id}/analyze", headers=headers)
        assert analyze_res.status_code == 200
        analysis_data = analyze_res.json()
        assert "summary" in analysis_data
        assert "trust_score" in analysis_data
        assert "risk_score" in analysis_data
        assert "trust_breakdown" in analysis_data
        assert "risk_assessment" in analysis_data
        assert len(analysis_data["recommendation"]["explanations"]) > 0

        rec_id = analysis_data["recommendation"]["id"]

        # 3. Judge Review Recommendation
        review_res = await async_client.post(
            f"/api/v1/ai/recommendations/{rec_id}/review?action=approved",
            headers=headers,
        )
        assert review_res.status_code == 200
        assert review_res.json()["status"] == "approved"
