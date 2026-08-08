"""
VADP Risk Scoring Engine
=============================

Multi-factor risk assessment evaluating case complexity, unverified evidence, procedural delays, and security policy restrictions.
"""

from __future__ import annotations

from app.ai.schemas import RiskAssessmentSchema, RiskFeatureSchema


class RiskScoringEngine:
    """Multi-factor risk engine."""

    @classmethod
    def evaluate_risk(
        cls,
        case_priority: str,
        unverified_evidence_count: int,
        has_policy_restriction: bool = False,
        case_age_days: int = 1,
    ) -> RiskAssessmentSchema:
        """
        Evaluate overall risk score bounded in [0.0, 1.0] and assign risk level.
        """
        # Feature 1: Case Priority (weight 0.40)
        priority_map = {"low": 0.20, "medium": 0.45, "high": 0.75, "critical": 0.95}
        val_priority = priority_map.get(case_priority.lower(), 0.50)
        w_priority = 0.40
        c_priority = val_priority * w_priority

        # Feature 2: Unverified Evidence (weight 0.35)
        val_evidence = min(1.0, unverified_evidence_count * 0.35)
        w_evidence = 0.35
        c_evidence = val_evidence * w_evidence

        # Feature 3: Policy Restriction (weight 0.15)
        val_policy = 0.85 if has_policy_restriction else 0.10
        w_policy = 0.15
        c_policy = val_policy * w_policy

        # Feature 4: Case Latency (weight 0.10)
        val_latency = min(1.0, case_age_days / 365.0)
        w_latency = 0.10
        c_latency = val_latency * w_latency

        overall_score = c_priority + c_evidence + c_policy + c_latency
        overall_score = round(max(0.0, min(1.0, overall_score)), 3)

        # Risk level tier classification
        if overall_score >= 0.75:
            risk_level = "critical"
        elif overall_score >= 0.50:
            risk_level = "high"
        elif overall_score >= 0.25:
            risk_level = "medium"
        else:
            risk_level = "low"

        features = [
            RiskFeatureSchema(name="Case Priority Level", value=round(val_priority, 2), weight=w_priority, contribution=round(c_priority, 3)),
            RiskFeatureSchema(name="Unverified Evidence Count", value=round(val_evidence, 2), weight=w_evidence, contribution=round(c_evidence, 3)),
            RiskFeatureSchema(name="Policy Restriction Flag", value=round(val_policy, 2), weight=w_policy, contribution=round(c_policy, 3)),
            RiskFeatureSchema(name="Procedural Case Latency", value=round(val_latency, 2), weight=w_latency, contribution=round(c_latency, 3)),
        ]

        return RiskAssessmentSchema(
            overall_score=overall_score,
            risk_level=risk_level,
            features=features,
        )
