"""
Nyaya-ZTA AI Engine Router
==========================

REST API endpoints for Explainable AI (XAI) Judicial Decision Support:
  - POST /api/v1/ai/cases/{case_id}/analyze
  - GET  /api/v1/ai/cases/{case_id}/recommendations
  - POST /api/v1/ai/recommendations/{id}/review
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import (
    AIRecommendationResponseSchema,
    CaseAnalysisResponseSchema,
)
from app.ai.service import AIService
from app.auth.dependencies import get_current_user, require_role
from app.auth.models import User
from app.db.session import get_db_session

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/cases/{case_id}/analyze",
    response_model=CaseAnalysisResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Run full AI case analysis & SHAP explainability",
    description="Analyze case using RAG, compute Trust Score formula, Risk Assessment, and SHAP feature importance.",
)
async def analyze_case(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> CaseAnalysisResponseSchema:
    service = AIService(db)
    return await service.analyze_case(case_id)


@router.get(
    "/cases/{case_id}/recommendations",
    response_model=list[AIRecommendationResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List AI recommendations for case",
    description="Retrieve all AI decision support recommendations and SHAP explanations for a case.",
)
async def list_recommendations(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[AIRecommendationResponseSchema]:
    service = AIService(db)
    return await service.list_recommendations_for_case(case_id)


@router.post(
    "/recommendations/{recommendation_id}/review",
    response_model=AIRecommendationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Review AI recommendation",
    description="Judge review action (approve, reject, or flag) on an AI recommendation.",
    dependencies=[Depends(require_role("judge"))],
)
async def review_recommendation(
    recommendation_id: str,
    action: str = "approved",  # approved | rejected | flagged
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AIRecommendationResponseSchema:
    service = AIService(db)
    return await service.review_recommendation(recommendation_id, current_user.id, action)
