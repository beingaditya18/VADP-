"""
VADP AI Model Drift Detector
==================================

Monitors real-time prediction performance and detects model degradation/drift over time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.ai.schemas import DriftCheckSchema
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelDriftDetector:
    """Detect model accuracy & confidence degradation over rolling prediction windows."""

    baseline_accuracy: float = 0.78
    drift_threshold: float = 0.10  # 10% degradation trigger
    _recent_predictions: list[dict[str, Any]] = []
    _max_window_size: int = 1000

    @classmethod
    def log_prediction(
        cls, confidence: float, correct: bool | None = None, model_version: str = "v1"
    ) -> None:
        """Log prediction outcome for real-time drift tracking."""
        cls._recent_predictions.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence": confidence,
                "correct": correct,
                "model_version": model_version,
            }
        )

        if len(cls._recent_predictions) > cls._max_window_size:
            cls._recent_predictions.pop(0)

    @classmethod
    def check_drift(cls) -> DriftCheckSchema:
        """Check rolling window for accuracy drift relative to baseline."""
        n_total = len(cls._recent_predictions)

        if n_total < 10:
            return DriftCheckSchema(
                drift_detected=False,
                baseline_accuracy=cls.baseline_accuracy,
                recent_accuracy=cls.baseline_accuracy,
                sample_count=n_total,
                recommendation="Insufficient prediction samples for drift check (min 10 required).",
                message="Model monitoring stable. Collecting prediction samples.",
            )

        # Filter predictions with explicit correctness feedback
        evaluated = [p for p in cls._recent_predictions if p.get("correct") is not None]

        if len(evaluated) < 5:
            # Fall back to confidence window mean if ground truth reviews are sparse
            confidences = [p["confidence"] for p in cls._recent_predictions]
            mean_conf = float(sum(confidences) / len(confidences))
            recent_acc = round(
                mean_conf * 0.90, 4
            )  # Estimated confidence accuracy proxy
        else:
            correct_count = sum(1 for p in evaluated if p["correct"] is True)
            recent_acc = round(correct_count / float(len(evaluated)), 4)

        drift = (cls.baseline_accuracy - recent_acc) > cls.drift_threshold

        recommendation = (
            "Model retraining recommended immediately! Performance drop exceeded 10% threshold."
            if drift
            else "Model performance within normal distribution boundaries."
        )

        message = (
            f"Alert: Model performance dropped to {recent_acc * 100:.1f}% vs baseline {cls.baseline_accuracy * 100:.1f}%."
            if drift
            else f"Model operating normally at {recent_acc * 100:.1f}% accuracy."
        )

        if drift:
            logger.warning(message)

        return DriftCheckSchema(
            drift_detected=drift,
            baseline_accuracy=cls.baseline_accuracy,
            recent_accuracy=recent_acc,
            sample_count=n_total,
            recommendation=recommendation,
            message=message,
        )

    @classmethod
    def clear_history(cls) -> None:
        """Reset logged prediction history."""
        cls._recent_predictions.clear()
