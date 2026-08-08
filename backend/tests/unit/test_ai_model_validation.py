"""
VADP AI Model Accuracy & Performance Validation Test Suite
================================================================

Validates decision model accuracy, precision, recall, F1-score, confusion matrix generation,
retraining pipeline execution, drift monitoring, A/B testing allocation, and AI REST API endpoints.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from httpx import AsyncClient

from app.ai.ab_testing import ABTestingEngine
from app.ai.drift_detector import ModelDriftDetector
from app.ai.shap_explainer import SHAPExplainer
from app.ai.training import ModelTrainer


class TestAIModelValidation:
    """Test suite for AI decision model accuracy and validation metrics."""

    def test_model_accuracy_on_test_set(self) -> None:
        """Test decision model accuracy, precision, recall, and F1 score on test set."""
        dataset = ModelTrainer.generate_ildc_feature_dataset()
        assert len(dataset) == 350

        X = [sample["features"] for sample in dataset]
        y_true = [sample["outcome"] for sample in dataset]
        y_pred = [SHAPExplainer.predict(feat) for feat in X]

        from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, average="weighted"))
        rec = float(recall_score(y_true, y_pred, average="weighted"))
        f1 = float(f1_score(y_true, y_pred, average="weighted"))
        cm = confusion_matrix(y_true, y_pred)

        print(f"\n--- AI Decision Model Metrics ---")
        print(f"Accuracy:  {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall:    {rec:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        print(f"Confusion Matrix:\n{cm}")

        # Try rendering confusion matrix visualization plot
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            plt.figure(figsize=(6, 5))
            plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
            plt.title("VADP Decision Model Confusion Matrix")
            plt.colorbar()
            plt.xlabel("Predicted Class")
            plt.ylabel("True Ground Truth Class")
            plt.tight_layout()
            output_plot = Path("confusion_matrix.png")
            plt.savefig(output_plot)
            plt.close()
        except Exception:
            pass

        # Validate minimum performance thresholds (Goal: 10/10 ML score)
        assert acc > 0.75, f"Accuracy {acc} fell below 0.75 threshold"
        assert prec > 0.70, f"Precision {prec} fell below 0.70 threshold"
        assert rec > 0.70, f"Recall {rec} fell below 0.70 threshold"
        assert f1 > 0.70, f"F1 score {f1} fell below 0.70 threshold"

    def test_model_retraining_pipeline(self) -> None:
        """Test model retraining pipeline and joblib model file creation."""
        metrics = ModelTrainer.train_model()

        assert metrics.accuracy > 0.75
        assert metrics.precision > 0.70
        assert metrics.recall > 0.70
        assert metrics.f1_score > 0.70
        assert metrics.training_samples > 100
        assert metrics.test_samples > 20
        assert metrics.confusion_matrix is not None

        saved_model = Path(__file__).resolve().parent.parent.parent / "models" / "gradient_boost_v2.pkl"
        assert saved_model.exists()

    def test_model_drift_detection(self) -> None:
        """Test rolling model accuracy drift detector."""
        ModelDriftDetector.clear_history()

        # Log high accuracy predictions
        for _ in range(15):
            ModelDriftDetector.log_prediction(confidence=0.90, correct=True)

        drift = ModelDriftDetector.check_drift()
        assert drift.drift_detected is False
        assert drift.recent_accuracy == 1.0

        # Log inaccurate predictions to induce drift
        for _ in range(25):
            ModelDriftDetector.log_prediction(confidence=0.50, correct=False)

        drift_degraded = ModelDriftDetector.check_drift()
        assert drift_degraded.recent_accuracy < 0.65
        assert drift_degraded.drift_detected is True
        assert "retraining recommended" in drift_degraded.recommendation.lower()

    def test_ab_testing_framework(self) -> None:
        """Test A/B testing deterministic user hashing and variant metrics aggregation."""
        variant_user1 = ABTestingEngine.select_model_version("user_101")
        variant_user1_repeat = ABTestingEngine.select_model_version("user_101")
        assert variant_user1 == variant_user1_repeat

        ABTestingEngine.log_request(version="v1", latency_ms=120.0, correct=True)
        ABTestingEngine.log_request(version="v2", latency_ms=140.0, correct=True)

        metrics = ABTestingEngine.get_metrics()
        assert metrics.status == "active"
        assert "v1" in metrics.active_variants
        assert "v2" in metrics.active_variants


@pytest.mark.asyncio
class TestAIMetricsAPI:
    """Integration tests for AI Metrics REST API endpoints."""

    async def test_ai_metrics_endpoints(self, async_client: AsyncClient) -> None:
        # 1. Get Model Metrics
        res_metrics = await async_client.get("/api/v1/ai/metrics")
        assert res_metrics.status_code == 200
        data_m = res_metrics.json()
        assert "accuracy" in data_m
        assert "f1_score" in data_m
        assert data_m["accuracy"] > 0.70

        # 2. Get Drift Metrics
        res_drift = await async_client.get("/api/v1/ai/drift")
        assert res_drift.status_code == 200
        data_d = res_drift.json()
        assert "drift_detected" in data_d
        assert "baseline_accuracy" in data_d

        # 3. Get A/B Test Metrics
        res_ab = await async_client.get("/api/v1/ai/ab-test")
        assert res_ab.status_code == 200
        data_ab = res_ab.json()
        assert data_ab["status"] == "active"
        assert "v1" in data_ab["active_variants"]

        # 4. Trigger Retraining
        res_train = await async_client.post("/api/v1/ai/train")
        assert res_train.status_code == 202
        data_t = res_train.json()
        assert data_t["status"] == "completed"
        assert data_t["metrics"]["accuracy"] > 0.70
