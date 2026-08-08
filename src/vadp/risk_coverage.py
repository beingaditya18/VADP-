"""
Selective Prediction & Learning-to-Defer Module for VADP Verification Contracts.

Reframes Human Override Coverage (HOC) under Chow's Rule (1970) and 
Mozannar & Sontag (2020) reject-option / learning-to-defer literature.

Instead of an arbitrary threshold ratio, VADP instantiates selective prediction:
- Prediction g(x) is accepted when TrustScore(x) >= tau
- Prediction is deferred to Human Review (HITL) when TrustScore(x) < tau
- Coverage C(tau) = P(TrustScore(x) >= tau)
- Risk R(tau) = E[Loss(g(x), y) | TrustScore(x) >= tau]
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from pydantic import BaseModel


class RiskCoveragePoint(BaseModel):
    threshold: float
    coverage: float
    risk: float
    accuracy: float
    deferred_count: int
    evaluated_count: int


class SelectivePredictionMetrics(BaseModel):
    total_samples: int
    optimal_threshold: float
    target_risk: float
    achieved_coverage: float
    achieved_risk: float
    achieved_accuracy: float
    auc_risk_coverage: float
    curve: List[RiskCoveragePoint]


class SelectivePredictionEvaluator:
    """
    Evaluates risk-coverage trade-offs across trust score thresholds
    and computes optimal deferral policy parameters.
    """

    def __init__(self, trust_scores: List[float], correctness_labels: List[int]):
        """
        :param trust_scores: List of normalized trust scores [0.0, 1.0] for model outputs
        :param correctness_labels: List of binary correctness indicators (1 = correct, 0 = error/hallucination)
        """
        if len(trust_scores) != len(correctness_labels):
            raise ValueError("trust_scores and correctness_labels must have equal length")
        
        self.scores = np.array(trust_scores, dtype=float)
        self.labels = np.array(correctness_labels, dtype=int)
        self.n = len(trust_scores)

    def compute_curve(self, num_thresholds: int = 50) -> List[RiskCoveragePoint]:
        """Compute Risk-Coverage points across a grid of trust thresholds tau in [0, 1]."""
        thresholds = np.linspace(0.0, 1.0, num_thresholds)
        curve: List[RiskCoveragePoint] = []

        for tau in thresholds:
            accepted_mask = self.scores >= tau
            accepted_count = int(np.sum(accepted_mask))
            deferred_count = self.n - accepted_count

            if accepted_count == 0:
                coverage = 0.0
                accuracy = 1.0
                risk = 0.0
            else:
                coverage = float(accepted_count / self.n)
                accuracy = float(np.mean(self.labels[accepted_mask]))
                risk = float(1.0 - accuracy)

            curve.append(
                RiskCoveragePoint(
                    threshold=float(round(tau, 4)),
                    coverage=float(round(coverage, 4)),
                    risk=float(round(risk, 4)),
                    accuracy=float(round(accuracy, 4)),
                    deferred_count=deferred_count,
                    evaluated_count=accepted_count,
                )
            )

        return curve

    def evaluate(self, target_risk: float = 0.05, num_thresholds: int = 100) -> SelectivePredictionMetrics:
        """
        Finds the minimal threshold tau* that satisfies Risk(tau*) <= target_risk,
        and computes the Area Under the Risk-Coverage Curve (AURCC).
        """
        curve = self.compute_curve(num_thresholds=num_thresholds)

        # Filter valid points satisfying target risk constraint
        valid_points = [p for p in curve if p.evaluated_count > 0 and p.risk <= target_risk]

        if valid_points:
            # Pick highest coverage among valid points
            optimal_point = max(valid_points, key=lambda p: p.coverage)
        else:
            # Fallback to point with minimal risk if target risk is unrealistically tight
            non_empty_points = [p for p in curve if p.evaluated_count > 0]
            optimal_point = min(non_empty_points, key=lambda p: p.risk) if non_empty_points else curve[0]

        # Compute AURCC via trapezoidal integration of risk over coverage
        coverages = [p.coverage for p in curve if p.evaluated_count > 0]
        risks = [p.risk for p in curve if p.evaluated_count > 0]
        
        # Sort by coverage ascending for integration
        if coverages:
            sorted_indices = np.argsort(coverages)
            cov_sorted = np.array(coverages)[sorted_indices]
            risk_sorted = np.array(risks)[sorted_indices]
            trapz_func = getattr(np, "trapezoid", getattr(np, "trapz", None))
            aurcc = float(round(trapz_func(risk_sorted, cov_sorted), 4))
        else:
            aurcc = 0.0

        return SelectivePredictionMetrics(
            total_samples=self.n,
            optimal_threshold=optimal_point.threshold,
            target_risk=target_risk,
            achieved_coverage=optimal_point.coverage,
            achieved_risk=optimal_point.risk,
            achieved_accuracy=optimal_point.accuracy,
            auc_risk_coverage=aurcc,
            curve=curve,
        )


def evaluate_deferral_decision(trust_score: float, threshold: float = 0.75) -> Dict[str, Any]:
    """
    Helper function for VADP pipeline: decides whether recommendation is accepted
    or deferred to Human Review under selective prediction framework.
    """
    should_defer = trust_score < threshold
    return {
        "framing": "selective_prediction_learning_to_defer",
        "trust_score": trust_score,
        "deferral_threshold": threshold,
        "action": "defer_to_human_review" if should_defer else "auto_accept_with_audit",
        "selective_prediction_status": "DEFERRED" if should_defer else "ACCEPTED",
        "theoretical_basis": "Chow's Rule (1970) / Mozannar & Sontag (2020)",
    }
