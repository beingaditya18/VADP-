"""
VADP SHAP Explainer Module
===============================

Computes genuine SHAP (SHapley Additive exPlanations) values for Explainable AI (XAI)
using shap.TreeExplainer over a trained judicial risk decision model.
Renders positive (supports decision) and negative (opposes/risks decision) feature contributions.
"""

from __future__ import annotations

import numpy as np
import shap
from sklearn.ensemble import GradientBoostingClassifier

from app.ai.schemas import ContributingFactorSchema, SHAPValueSchema


class SHAPExplainer:
    """SHAP explainer using genuine game-theoretic Shapley value computation."""

    _model: GradientBoostingClassifier | None = None
    _explainer: shap.TreeExplainer | None = None
    _feature_names = [
        "Evidence Cryptographic Integrity",
        "Statutory Precedent Alignment",
        "Unverified Evidence Penalty",
        "Procedural Delay Factor",
    ]

    @classmethod
    def _init_model_and_explainer(cls) -> None:
        """Train or load baseline tree ensemble and initialize shap.TreeExplainer."""
        if cls._model is not None and cls._explainer is not None:
            return

        # Check if saved trained model exists
        from pathlib import Path

        import joblib

        model_path = Path(__file__).resolve().parent.parent / "models" / "gradient_boost_v2.pkl"

        if model_path.exists():
            try:
                cls._model = joblib.load(model_path)
                cls._explainer = shap.TreeExplainer(cls._model)
                return
            except Exception:
                pass

        # Generate synthetic judicial feature dataset for model initialization
        np.random.seed(42)
        X_train = np.random.uniform(
            low=[0.0, 0.0, 0.0, 0.0],
            high=[1.0, 1.0, 5.0, 1.0],
            size=(200, 4),
        )
        # Target: 1 (High Risk), 0 (Low Risk)
        y_train = (
            (X_train[:, 0] < 0.5) * 0.4
            + (X_train[:, 1] < 0.5) * 0.3
            + (X_train[:, 2] > 1.0) * 0.2
            + (X_train[:, 3] > 0.4) * 0.1
        ) > 0.4
        y_train = y_train.astype(int)

        cls._model = GradientBoostingClassifier(n_estimators=30, max_depth=3, random_state=42)
        cls._model.fit(X_train, y_train)

        # Initialize official SHAP TreeExplainer
        cls._explainer = shap.TreeExplainer(cls._model)

    @classmethod
    def predict(cls, features: list[float]) -> int:
        """Predict risk/intervention outcome label (1 or 0) using trained decision model."""
        cls._init_model_and_explainer()
        assert cls._model is not None
        instance = np.array([features])
        return int(cls._model.predict(instance)[0])

    @classmethod
    def compute_shap_explanations(
        cls,
        evidence_quality: float,
        precedent_match: float,
        unverified_evidence: int,
        procedural_delay: float = 0.2,
    ) -> tuple[list[SHAPValueSchema], dict[str, float], list[ContributingFactorSchema]]:
        """
        Compute genuine SHAP values using shap.TreeExplainer over input feature vector.
        """
        cls._init_model_and_explainer()
        assert cls._explainer is not None

        # Input feature vector
        instance = np.array(
            [[evidence_quality, precedent_match, float(unverified_evidence), procedural_delay]]
        )

        # Compute raw Shapley values
        shap_raw = cls._explainer.shap_values(instance)
        if isinstance(shap_raw, list):
            # Binary classification: extract array for positive class
            shap_vec = shap_raw[1][0] if len(shap_raw) > 1 else shap_raw[0][0]
        elif len(shap_raw.shape) == 3:
            shap_vec = shap_raw[0, :, 1]
        else:
            shap_vec = shap_raw[0]

        feature_values_str = [
            f"{int(evidence_quality * 100)}%",
            f"{int(precedent_match * 100)}%",
            str(unverified_evidence),
            f"{int(procedural_delay * 100)}%",
        ]

        shap_values = []
        for name, val, f_val in zip(cls._feature_names, shap_vec, feature_values_str, strict=False):
            # In risk modeling, negative SHAP score reduces risk (supports security/integrity)
            direction = "positive" if val <= 0 else "negative"
            shap_values.append(
                SHAPValueSchema(
                    feature_name=name,
                    shap_value=round(float(val), 3),
                    feature_value=f_val,
                    contribution_direction=direction,
                )
            )

        importance = {s.feature_name: abs(s.shap_value) for s in shap_values}

        factors = []
        for s in shap_values:
            impact = (
                "high"
                if abs(s.shap_value) > 0.10
                else "medium"
                if abs(s.shap_value) > 0.03
                else "low"
            )
            direction = (
                "decreases_risk" if s.contribution_direction == "positive" else "increases_risk"
            )
            factors.append(
                ContributingFactorSchema(
                    factor=s.feature_name,
                    impact=impact,
                    direction=direction,
                    explanation=f"Shapley attribution: {s.shap_value:+.3f} (Feature Value: {s.feature_value})",
                )
            )

        return shap_values, importance, factors
