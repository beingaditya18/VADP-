"""
Nyaya-ZTA Case Service
======================

Business logic layer for case filings, status transitions, assignments, and events.
Decoupled from FastAPI router layer.
"""

from __future__ import annotations

import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case, CaseEvent, CaseParty
from app.cases.repository import CaseRepository
from app.cases.schemas import (
    CaseCreateSchema,
    CaseEventCreateSchema,
    CaseEventResponseSchema,
    CaseListResponseSchema,
    CaseResponseSchema,
    CaseUpdateSchema,
)
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class CaseService:
    """Service encapsulating case management workflows."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CaseRepository(db)

    async def file_case(self, schema: CaseCreateSchema, filed_by_id: str) -> CaseResponseSchema:
        """
        File a new judicial case.
        """
        case_number = await self.repo.generate_unique_case_number(schema.case_type)

        case = Case(
            case_number=case_number,
            title=schema.title,
            description=schema.description,
            case_type=schema.case_type,
            priority=schema.priority.value,
            filed_by=filed_by_id,
            court_id=schema.court_id,
            status="filed",
        )

        parties = [
            CaseParty(
                party_name=p.party_name,
                party_type=p.party_type.value,
                user_id=p.user_id,
            )
            for p in schema.parties
        ]

        created_case = await self.repo.create_case(case, parties)
        logger.info("Case filed successfully", extra={"case_id": created_case.id, "case_number": case_number})
        return CaseResponseSchema.model_validate(created_case)

    async def get_case_by_id(self, case_id: str) -> CaseResponseSchema:
        """
        Retrieve case by ID.
        """
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(message=f"Case with ID '{case_id}' not found.")
        return CaseResponseSchema.model_validate(case)

    async def list_cases(
        self,
        user_id: str | None = None,
        role: str | None = None,
        status: str | None = None,
        case_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CaseListResponseSchema:
        """
        List cases with role-based scoping and pagination.
        """
        items, total = await self.repo.list_cases(
            user_id=user_id,
            role=role,
            status=status,
            case_type=case_type,
            page=page,
            page_size=page_size,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        response_items = [CaseResponseSchema.model_validate(c) for c in items]

        return CaseListResponseSchema(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_case(
        self, case_id: str, schema: CaseUpdateSchema, performed_by_id: str
    ) -> CaseResponseSchema:
        """
        Update case status, assignment, or details.
        """
        updates = schema.model_dump(exclude_unset=True)
        if "status" in updates and updates["status"]:
            updates["status"] = updates["status"].value
        if "priority" in updates and updates["priority"]:
            updates["priority"] = updates["priority"].value

        updated_case = await self.repo.update_case(case_id, updates, performed_by_id)
        if not updated_case:
            raise NotFoundError(message=f"Case with ID '{case_id}' not found.")

        logger.info("Case updated", extra={"case_id": case_id, "performed_by": performed_by_id})
        return CaseResponseSchema.model_validate(updated_case)

    async def add_event(
        self, case_id: str, schema: CaseEventCreateSchema, performed_by_id: str
    ) -> CaseEventResponseSchema:
        """
        Log a timeline event for a case.
        """
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(message=f"Case with ID '{case_id}' not found.")

        event = await self.repo.add_case_event(
            case_id=case_id,
            event_type=schema.event_type,
            description=schema.description,
            performed_by=performed_by_id,
            data=schema.event_data,
        )
        return CaseEventResponseSchema.model_validate(event)
