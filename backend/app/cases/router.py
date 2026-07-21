"""
Nyaya-ZTA Case Router
=====================

REST API endpoints for case management:
  - POST /api/v1/cases
  - GET  /api/v1/cases
  - GET  /api/v1/cases/{id}
  - PUT  /api/v1/cases/{id}
  - POST /api/v1/cases/{id}/events
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.cases.schemas import (
    CaseCreateSchema,
    CaseEventCreateSchema,
    CaseEventResponseSchema,
    CaseListResponseSchema,
    CaseResponseSchema,
    CaseUpdateSchema,
)
from app.cases.service import CaseService
from app.db.session import get_db_session

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post(
    "",
    response_model=CaseResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="File a new case",
    description="Create a new case filing with parties and initial timeline event.",
)
async def file_case(
    schema: CaseCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CaseResponseSchema:
    service = CaseService(db)
    return await service.file_case(schema, current_user.id)


@router.get(
    "",
    response_model=CaseListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="List cases",
    description="Retrieve cases with role-scoped filtering and pagination.",
)
async def list_cases(
    status_filter: str | None = Query(None, alias="status"),
    case_type: str | None = Query(None, alias="case_type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CaseListResponseSchema:
    service = CaseService(db)
    return await service.list_cases(
        user_id=current_user.id,
        role=current_user.role,
        status=status_filter,
        case_type=case_type,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{case_id}",
    response_model=CaseResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get case details",
    description="Retrieve full details for a case including parties and event timeline.",
)
async def get_case_details(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> CaseResponseSchema:
    service = CaseService(db)
    return await service.get_case_by_id(case_id)


@router.put(
    "/{case_id}",
    response_model=CaseResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Update case details or status",
    description="Update status, priority, judge assignment, lawyer assignment, or next hearing date.",
)
async def update_case(
    case_id: str,
    schema: CaseUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CaseResponseSchema:
    service = CaseService(db)
    return await service.update_case(case_id, schema, current_user.id)


@router.post(
    "/{case_id}/events",
    response_model=CaseEventResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add timeline event",
    description="Log a custom timeline audit event for a case.",
)
async def add_case_event(
    case_id: str,
    schema: CaseEventCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CaseEventResponseSchema:
    service = CaseService(db)
    return await service.add_event(case_id, schema, current_user.id)
