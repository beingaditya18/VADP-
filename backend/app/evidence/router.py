"""
Nyaya-ZTA Evidence Router
=========================

REST API endpoints for evidence registration and integrity verification:
  - POST /api/v1/evidence
  - GET  /api/v1/evidence/case/{case_id}
  - POST /api/v1/evidence/{id}/verify
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.db.session import get_db_session
from app.evidence.schemas import (
    EvidenceCreateSchema,
    EvidenceResponseSchema,
    EvidenceVerificationResultSchema,
)
from app.evidence.service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post(
    "",
    response_model=EvidenceResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register evidence record",
    description="Register an uploaded document as legal case evidence with chain of custody tracking.",
)
async def create_evidence(
    schema: EvidenceCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EvidenceResponseSchema:
    service = EvidenceService(db)
    return await service.create_evidence(schema, current_user.id)


@router.get(
    "/case/{case_id}",
    response_model=list[EvidenceResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List case evidence",
    description="Retrieve all evidence records and chain of custody logs for a case.",
)
async def list_evidence(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[EvidenceResponseSchema]:
    service = EvidenceService(db)
    return await service.list_case_evidence(case_id)


@router.post(
    "/{evidence_id}/verify",
    response_model=EvidenceVerificationResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Verify evidence integrity",
    description="Cryptographically recompute file SHA-256 on disk and compare against recorded custody hash.",
)
async def verify_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EvidenceVerificationResultSchema:
    service = EvidenceService(db)
    return await service.verify_evidence(evidence_id, current_user.id)
