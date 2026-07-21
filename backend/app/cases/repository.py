"""
Nyaya-ZTA Case Repository
=========================

Data access layer for Case, CaseParty, and CaseEvent entities using SQLAlchemy 2.x async API.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cases.models import Case, CaseEvent, CaseParty


class CaseRepository:
    """Repository pattern implementation for Case domain operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create_case(self, case: Case, parties: list[CaseParty]) -> Case:
        """Store a new case filing with its associated parties."""
        self.db.add(case)
        await self.db.flush()

        for party in parties:
            party.case_id = case.id
            self.db.add(party)

        # Automatically log initial timeline event
        initial_event = CaseEvent(
            case_id=case.id,
            event_type="case_filed",
            description=f"Case filed with priority '{case.priority}'",
            performed_by=case.filed_by,
            event_data={"case_type": case.case_type},
        )
        self.db.add(initial_event)
        await self.db.flush()

        return await self.get_by_id(case.id)  # Returns with preloaded relationships

    async def get_by_id(self, case_id: str) -> Case | None:
        """Fetch case details by ID, eagerly loading parties and events."""
        stmt = (
            select(Case)
            .where(Case.id == case_id, Case.is_deleted == False)  # noqa: E712
            .options(
                selectinload(Case.parties),
                selectinload(Case.events),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_case_number(self, case_number: str) -> Case | None:
        """Fetch case by case_number string."""
        stmt = (
            select(Case)
            .where(Case.case_number == case_number, Case.is_deleted == False)  # noqa: E712
            .options(selectinload(Case.parties), selectinload(Case.events))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_cases(
        self,
        user_id: str | None = None,
        role: str | None = None,
        status: str | None = None,
        case_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Case], int]:
        """
        List cases with role-scoped filtering and pagination.
        """
        query = select(Case).where(Case.is_deleted == False)  # noqa: E712

        # Role-based scoping:
        if role == "citizen":
            query = query.where(Case.filed_by == user_id)
        elif role == "lawyer":
            query = query.where((Case.assigned_lawyer == user_id) | (Case.filed_by == user_id))
        elif role == "judge":
            query = query.where((Case.assigned_judge == user_id) | (Case.assigned_judge.is_(None)))

        if status:
            query = query.where(Case.status == status)
        if case_type:
            query = query.where(Case.case_type == case_type)

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        paginated_stmt = (
            query.order_by(Case.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .options(selectinload(Case.parties), selectinload(Case.events))
        )
        result = await self.db.execute(paginated_stmt)
        items = result.scalars().all()

        return items, total

    async def update_case(self, case_id: str, updates: dict, performed_by: str) -> Case | None:
        """Update case details and log timeline event."""
        case = await self.get_by_id(case_id)
        if not case:
            return None

        old_status = case.status
        for field, value in updates.items():
            if value is not None and hasattr(case, field):
                setattr(case, field, value)

        case.updated_at = datetime.now(timezone.utc)

        # Log event if status changed
        if "status" in updates and updates["status"] != old_status:
            event = CaseEvent(
                case_id=case.id,
                event_type="status_changed",
                description=f"Case status changed from '{old_status}' to '{case.status}'",
                performed_by=performed_by,
                event_data={"old_status": old_status, "new_status": case.status},
            )
            self.db.add(event)
            case.events.append(event)

        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def add_case_event(self, case_id: str, event_type: str, description: str | None, performed_by: str, data: dict) -> CaseEvent:
        """Add a custom timeline event for a case."""
        event = CaseEvent(
            case_id=case_id,
            event_type=event_type,
            description=description,
            performed_by=performed_by,
            event_data=data,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def generate_unique_case_number(self, case_type: str) -> str:
        """Generate a unique case number e.g. NYA-CIV-2026-X8F9."""
        prefix = case_type[:3].upper()
        year = datetime.now().year
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"NYA-{prefix}-{year}-{rand_str}"
