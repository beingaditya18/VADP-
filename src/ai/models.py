"""
VADP AI Engine Models
==========================

SQLAlchemy 2.x declarative models for AIRecommendations and AIExplanations.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class AIRecommendation(Base, UUIDMixin, TimestampMixin):
    """
    AI-generated judicial decision support recommendation record.
    """

    __tablename__ = "ai_recommendations"

    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(100), nullable=False)  # summary, judgment_support, risk_assessment
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(100), default="nyaya-shap-v1.0", nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String(100), default="groq-llama3", nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, approved, rejected, flagged
    reviewed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata_", JSON, default=dict, nullable=False)

    # Relationship
    explanations: Mapped[list[AIExplanation]] = relationship("AIExplanation", back_populates="recommendation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AIRecommendation(id={self.id}, case_id={self.case_id}, trust={self.trust_score:.2f})>"


class AIExplanation(Base, UUIDMixin, TimestampMixin):
    """
    Explainability breakdown containing SHAP feature values, trust weights, and bias markers.
    """

    __tablename__ = "ai_explanations"

    recommendation_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_recommendations.id", ondelete="CASCADE"), index=True, nullable=False)
    explanation_type: Mapped[str] = mapped_column(String(100), default="shap_feature_importance", nullable=False)
    shap_values: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    feature_importance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    contributing_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    natural_language_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    bias_markers: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Relationship
    recommendation: Mapped[AIRecommendation] = relationship("AIRecommendation", back_populates="explanations")

    def __repr__(self) -> str:
        return f"<AIExplanation(id={self.id}, rec_id={self.recommendation_id})>"
