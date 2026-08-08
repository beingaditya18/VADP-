"""
VADP Case Router
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
    BailOutcomeEstimatorSchema,
    CaseCreateSchema,
    CaseEventCreateSchema,
    CaseEventResponseSchema,
    CaseListResponseSchema,
    CaseResponseSchema,
    CaseTimelineResponseSchema,
    CaseUpdateSchema,
    HearingScheduleCreateSchema,
    HearingScheduleResponseSchema,
    MegaCaseSummarySchema,
    PrecedentRadarResponseSchema,
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
    search: str | None = Query(None),
    court: str | None = Query(None),
    year: int | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
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
        search=search,
        court=court,
        year=year,
        sort_by=sort_by,
        sort_order=sort_order,
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


@router.get(
    "/{case_id}/timeline",
    response_model=CaseTimelineResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get case milestone timeline",
    description="Retrieve unified chronological timeline of filings, events, evidence uploads, and hearing dates.",
)
async def get_case_timeline(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> CaseTimelineResponseSchema:
    service = CaseService(db)
    return await service.get_case_timeline(case_id)


@router.post(
    "/{case_id}/hearings",
    response_model=HearingScheduleResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule next court hearing",
    description="Schedule a hearing, assign courtroom, log case event, and send alerts to Judge, Lawyer, and Citizen.",
)
async def schedule_hearing(
    case_id: str,
    schema: HearingScheduleCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> HearingScheduleResponseSchema:
    schema.case_id = case_id
    service = CaseService(db)
    return await service.schedule_hearing(schema, current_user.id)


@router.get(
    "/{case_id}/mega-summary",
    response_model=MegaCaseSummarySchema,
    status_code=status.HTTP_200_OK,
    summary="Generate Mega-Case AI summary",
    description="Generates executive legal summary, key disputes, arguments, and recommended next steps for large cases.",
)
async def get_mega_summary(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> MegaCaseSummarySchema:
    from app.ai.precedent_radar import MegaCaseSummarizerEngine
    service = CaseService(db)
    case_res = await service.get_case_by_id(case_id)
    return MegaCaseSummarizerEngine.generate_mega_summary(
        case_id=case_res.id,
        case_number=case_res.case_number,
        title=case_res.title,
        description=case_res.description,
        case_type=case_res.case_type,
    )


@router.get(
    "/{case_id}/precedent-radar",
    response_model=PrecedentRadarResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Scan precedent contradictions",
    description="Analyzes case arguments against RAG precedent vector DB to flag legal contradictions and overruling cases.",
)
async def get_precedent_radar(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> PrecedentRadarResponseSchema:
    from app.ai.precedent_radar import PrecedentRadarEngine
    service = CaseService(db)
    case_res = await service.get_case_by_id(case_id)
    return PrecedentRadarEngine.analyze_precedents(case_id=case_res.id, case_title=case_res.title)


@router.get(
    "/{case_id}/bail-estimator",
    response_model=BailOutcomeEstimatorSchema,
    status_code=status.HTTP_200_OK,
    summary="Estimate bail / outcome probability with SHAP",
    description="Predicts interim order / bail likelihood and returns SHAP feature contribution factors for judicial explainability.",
)
async def get_bail_estimator(
    case_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> BailOutcomeEstimatorSchema:
    from app.ai.precedent_radar import BailOutcomeEstimatorEngine
    service = CaseService(db)
    case_res = await service.get_case_by_id(case_id)
    return BailOutcomeEstimatorEngine.estimate_outcome(case_id=case_res.id, priority=case_res.priority.value)

