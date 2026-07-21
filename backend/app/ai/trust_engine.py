"""
Nyaya-ZTA Trust Scoring Engine
==============================

Computes formal, mathematically grounded Trust Scores for AI judicial decision support.
Trust Score Formula:
  Trust = α * S_model + β * S_evidence + γ * S_source + δ * S_consistency

Constraints:
  α + β + γ + δ = 1.0
  Default weights: α=0.35 (model confidence), β=0.35 (evidence integrity),
                   γ=0.15 (source reliability), δ=0.15 (jurisprudential consistency).
"""

from __future__ import annotations

from app.ai.schemas import TrustScoreBreakdownSchema


class TrustScoringEngine:
    """Formal Trust Scoring Engine."""

    ALPHA = 0.35  # Model Confidence Weight
    BETA = 0.35   # Evidence Quality & Hash Integrity Weight
    GAMMA = 0.15  # Source Reliability Weight
    DELTA = 0.15  # Consistency Weight

    @classmethod
    def calculate_trust_score(
        cls,
        model_confidence: float,
        evidence_quality: float,
        source_reliability: float = 0.90,
        consistency: float = 0.88,
    ) -> TrustScoreBreakdownSchema:
        """
        Calculate overall trust score bounded in [0.0, 1.0].
        """
        # Clamp inputs to [0.0, 1.0]
        s_model = max(0.0, min(1.0, model_confidence))
        s_evidence = max(0.0, min(1.0, evidence_quality))
        s_source = max(0.0, min(1.0, source_reliability))
        s_consistency = max(0.0, min(1.0, consistency))

        overall = (
            cls.ALPHA * s_model
            + cls.BETA * s_evidence
            + cls.GAMMA * s_source
            + cls.DELTA * s_consistency
        )

        return TrustScoreBreakdownSchema(
            overall=round(overall, 3),
            model_confidence=round(s_model, 3),
            evidence_quality=round(s_evidence, 3),
            source_reliability=round(s_source, 3),
            consistency=round(s_consistency, 3),
            weights={
                "alpha": cls.ALPHA,
                "beta": cls.BETA,
                "gamma": cls.GAMMA,
                "delta": cls.DELTA,
            },
        )
