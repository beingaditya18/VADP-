"""
NIST SP 800-207 Continuous Verification & Adaptive Session Risk Evaluation Engine.

Upgrades static one-shot ABAC evaluation into continuous Zero-Trust session evaluation:
R_session(t) = R_0 * exp(lambda * delta_t) + sum(delta_R_anomaly)
T_session(t) = 1.0 - R_session(t)
"""

from typing import Dict, Any, Optional
import math
import time
from pydantic import BaseModel, Field


class ContinuousSessionState(BaseModel):
    session_id: str
    user_id: str
    initial_risk_R0: float = Field(default=0.05, ge=0.0, le=1.0)
    decay_lambda: float = Field(
        default=0.01, description="Temporal risk accumulation decay constant"
    )
    last_evaluated_timestamp: float
    accumulated_anomalies: float = Field(default=0.0)
    step_up_auth_required: bool = False


class ContinuousTrustEvaluator:
    """
    Evaluates continuous session risk and adaptive trust score per request.
    """

    def __init__(self, risk_threshold: float = 0.40):
        self.risk_threshold = risk_threshold

    def calculate_session_risk(
        self, state: ContinuousSessionState, current_time: Optional[float] = None
    ) -> Dict[str, Any]:
        t_now = current_time or time.time()
        delta_t_minutes = max(0.0, (t_now - state.last_evaluated_timestamp) / 60.0)

        # Exponential temporal risk accumulation: R_time = R0 * exp(lambda * delta_t)
        temporal_risk = state.initial_risk_R0 * math.exp(
            state.decay_lambda * delta_t_minutes
        )

        total_risk = min(1.0, max(0.0, temporal_risk + state.accumulated_anomalies))
        session_trust_score = float(round(1.0 - total_risk, 4))

        requires_reauth = total_risk >= self.risk_threshold

        return {
            "session_id": state.session_id,
            "user_id": state.user_id,
            "delta_t_minutes": float(round(delta_t_minutes, 2)),
            "session_risk_score": float(round(total_risk, 4)),
            "session_trust_score": session_trust_score,
            "step_up_auth_required": requires_reauth,
            "compliance_standard": "NIST SP 800-207 Continuous Verification",
        }

    def record_anomaly(
        self, state: ContinuousSessionState, anomaly_risk_delta: float
    ) -> ContinuousSessionState:
        """Adds an anomaly risk impulse to the session state."""
        state.accumulated_anomalies += anomaly_risk_delta
        if state.accumulated_anomalies >= self.risk_threshold:
            state.step_up_auth_required = True
        return state
