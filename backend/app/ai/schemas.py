"""
VADP AI Engine Schemas
===========================

Pydantic schemas for AI recommendations, SHAP feature importance, trust score breakdowns, and risk assessments.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SHAPValueSchema(BaseModel):
    feature_name: str
    shap_value: float
    feature_value: Any
    contribution_direction: str  # 'positive' | 'negative'


class ContributingFactorSchema(BaseModel):
    factor: str
    impact: str  # 'high' | 'medium' | 'low'
    direction: str  # 'increases_risk' | 'decreases_risk' | 'neutral'
    explanation: str


class TrustScoreBreakdownSchema(BaseModel):
    overall: float
    model_confidence: float
    evidence_quality: float
    source_reliability: float
    consistency: float
    weights: dict[str, float] = Field(
        default_factory=lambda: {"alpha": 0.35, "beta": 0.35, "gamma": 0.15, "delta": 0.15}
    )


class RiskFeatureSchema(BaseModel):
    name: str
    value: float
    weight: float
    contribution: float


class RiskAssessmentSchema(BaseModel):
    overall_score: float
    risk_level: str  # 'low' | 'medium' | 'high' | 'critical'
    features: list[RiskFeatureSchema]


class AIExplanationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    explanation_type: str
    shap_values: list[SHAPValueSchema]
    feature_importance: dict[str, float]
    contributing_factors: list[ContributingFactorSchema]
    natural_language_explanation: str | None = None
    bias_markers: list[str] = Field(default_factory=list)


class AIRecommendationResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    recommendation_type: str
    recommendation_text: str
    confidence_score: float
    trust_score: float
    risk_score: float
    status: str
    model_version: str | None = None
    llm_provider: str | None = None
    created_at: datetime
    explanations: list[AIExplanationResponseSchema] = Field(default_factory=list)
    trust_breakdown: TrustScoreBreakdownSchema | None = None
    risk_assessment: RiskAssessmentSchema | None = None


class CaseAnalysisResponseSchema(BaseModel):
    case_id: str
    summary: str
    trust_score: float
    risk_score: float
    risk_level: str
    recommendation: AIRecommendationResponseSchema
    trust_breakdown: TrustScoreBreakdownSchema
    risk_assessment: RiskAssessmentSchema
    verification_contract: Any | None = Field(
        default=None,
        description="VADP: Verification Contract generated for this analysis",
    )


class ModelMetricsSchema(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    test_samples: int
    last_trained: str
    dataset_source: str = "350 ILDC Supreme Court Judgments"
    confusion_matrix: list[list[int]] | None = None


class RetrainResponseSchema(BaseModel):
    message: str
    status: str
    metrics: ModelMetricsSchema | None = None


class DriftCheckSchema(BaseModel):
    drift_detected: bool
    baseline_accuracy: float
    recent_accuracy: float
    sample_count: int
    recommendation: str
    message: str | None = None


class ABTestVariantMetricsSchema(BaseModel):
    variant: str
    model_file: str
    traffic_percentage: float
    total_requests: int
    avg_latency_ms: float
    accuracy: float


class ABTestMetricsSchema(BaseModel):
    status: str
    active_variants: dict[str, ABTestVariantMetricsSchema]
    total_evaluations: int
