"""
VADP Trust Scoring Engine
==============================

Computes formal, mathematically grounded Trust Scores for AI judicial decision support.
Trust Score Formula:
  Trust = α * S_model + β * S_evidence + γ * S_source + δ * S_consistency

Constraints:
  α + β + γ + δ = 1.0
  Dynamic Logistic Regression Mode: Weights α, β, γ, δ are derived from normalized logistic
  regression coefficients fit on empirical judicial decision/approval ground truth.
  Default fallback weights: α=0.35 (model confidence), β=0.35 (evidence integrity),
                           γ=0.15 (source reliability), δ=0.15 (jurisprudential consistency).
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple
import numpy as np
from sklearn.linear_model import LogisticRegression

from app.ai.schemas import TrustScoreBreakdownSchema

logger = logging.getLogger(__name__)


class TrustScoringEngine:
    """Formal Trust Scoring Engine supporting fixed and logistic-regression fitted weights."""

    ALPHA = 0.35  # Model Confidence Weight
    BETA = 0.35   # Evidence Quality & Hash Integrity Weight
    GAMMA = 0.15  # Source Reliability Weight
    DELTA = 0.15  # Consistency Weight

    _dynamic_weights: Optional[Dict[str, float]] = None

    @classmethod
    def set_dynamic_weights(cls, alpha: float, beta: float, gamma: float, delta: float) -> None:
        """Sets dynamically fitted weights from Logistic Regression coefficients."""
        total = alpha + beta + gamma + delta
        if total <= 0:
            raise ValueError("Sum of weights must be positive")
        cls._dynamic_weights = {
            "alpha": round(alpha / total, 4),
            "beta": round(beta / total, 4),
            "gamma": round(gamma / total, 4),
            "delta": round(delta / total, 4),
        }
        logger.info(f"Updated Trust Engine dynamic weights via Logistic Regression: {cls._dynamic_weights}")

    @classmethod
    def fit_logistic_regression_weights(
        cls,
        X_features: np.ndarray,
        y_labels: np.ndarray,
    ) -> Dict[str, float]:
        """
        Fits LogisticRegression model on historical decision features:
          X = [s_model, s_evidence, s_source, s_consistency]
          y = binary judicial approval / ground truth decision (0 or 1)
        Extracts positive coefficients and normalizes them so sum(weights) == 1.0.
        """
        model = LogisticRegression(penalty="l2", C=1.0, random_state=42)
        model.fit(X_features, y_labels)

        coefs = model.coef_[0]
        pos_coefs = np.abs(coefs)
        norm_coefs = pos_coefs / np.sum(pos_coefs)

        weights = {
            "alpha": round(float(norm_coefs[0]), 4),
            "beta": round(float(norm_coefs[1]), 4),
            "gamma": round(float(norm_coefs[2]), 4),
            "delta": round(float(norm_coefs[3]), 4),
        }
        cls.set_dynamic_weights(**weights)
        return weights

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

        w = cls._dynamic_weights or {
            "alpha": cls.ALPHA,
            "beta": cls.BETA,
            "gamma": cls.GAMMA,
            "delta": cls.DELTA,
        }

        overall = (
            w["alpha"] * s_model
            + w["beta"] * s_evidence
            + w["gamma"] * s_source
            + w["delta"] * s_consistency
        )

        return TrustScoreBreakdownSchema(
            overall=round(overall, 3),
            model_confidence=round(s_model, 3),
            evidence_quality=round(s_evidence, 3),
            source_reliability=round(s_source, 3),
            consistency=round(s_consistency, 3),
            weights=w,
        )

