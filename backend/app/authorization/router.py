"""
Nyaya-ZTA Authorization Router
==============================

REST API endpoints for policy administration and access decision testing:
  - POST /api/v1/authorization/policies
  - GET  /api/v1/authorization/policies
  - POST /api/v1/authorization/evaluate
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import User
from app.authorization.schemas import (
    AccessDecisionResponse,
    AccessEvaluationRequest,
    PolicyCreateSchema,
    PolicyResponseSchema,
)
from app.authorization.service import AuthorizationService
from app.db.session import get_db_session

router = APIRouter(prefix="/authorization", tags=["authorization"])


@router.post(
    "/policies",
    response_model=PolicyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create authorization policy",
    description="Add a new RBAC + ABAC policy rule (Admin only).",
    dependencies=[Depends(require_role("admin"))],
)
async def create_policy(
    schema: PolicyCreateSchema,
    db: AsyncSession = Depends(get_db_session),
) -> PolicyResponseSchema:
    service = AuthorizationService(db)
    return await service.create_policy(schema)


@router.get(
    "/policies",
    response_model=list[PolicyResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List authorization policies",
    description="Retrieve all stored security policies (Admin only).",
    dependencies=[Depends(require_role("admin"))],
)
async def list_policies(
    db: AsyncSession = Depends(get_db_session),
) -> list[PolicyResponseSchema]:
    service = AuthorizationService(db)
    return await service.list_policies()


@router.post(
    "/evaluate",
    response_model=AccessDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate access decision",
    description="Test access control rules against PDP for current user and context.",
)
async def evaluate_access(
    request: AccessEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AccessDecisionResponse:
    service = AuthorizationService(db)
    return await service.evaluate_access(current_user, request)
