"""
VADP Case Service
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

    async def file_case(
        self, schema: CaseCreateSchema, filed_by_id: str
    ) -> CaseResponseSchema:
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
        logger.info(
            "Case filed successfully",
            extra={"case_id": created_case.id, "case_number": case_number},
        )
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
        search: str | None = None,
        court: str | None = None,
        year: int | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> CaseListResponseSchema:
        """
        List cases with role-based scoping, search, and pagination.
        """
        items, total = await self.repo.list_cases(
            user_id=user_id,
            role=role,
            status=status,
            case_type=case_type,
            search=search,
            court=court,
            year=year,
            sort_by=sort_by,
            sort_order=sort_order,
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

        logger.info(
            "Case updated", extra={"case_id": case_id, "performed_by": performed_by_id}
        )
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

    async def schedule_hearing(
        self, schema: HearingScheduleCreateSchema, scheduled_by_id: str
    ) -> HearingScheduleResponseSchema:
        """
        Schedule a new court hearing, update case next_hearing_date, and dispatch notifications.
        """
        from app.cases.models import HearingSchedule
        from app.notifications.schemas import NotificationCreateSchema
        from app.notifications.service import NotificationService

        case = await self.repo.get_by_id(schema.case_id)
        if not case:
            raise NotFoundError(message=f"Case with ID '{schema.case_id}' not found.")

        hearing = HearingSchedule(
            case_id=schema.case_id,
            scheduled_date=schema.scheduled_date,
            courtroom=schema.courtroom,
            hearing_type=schema.hearing_type,
            status="SCHEDULED",
            purpose=schema.purpose,
            judge_notes=schema.judge_notes,
            scheduled_by=scheduled_by_id,
        )
        self.db.add(hearing)

        # Update Case event
        await self.repo.add_case_event(
            case_id=schema.case_id,
            event_type="HEARING_SCHEDULED",
            description=f"Hearing '{schema.hearing_type}' scheduled for {schema.scheduled_date} in {schema.courtroom}",
            performed_by=scheduled_by_id,
            data={
                "courtroom": schema.courtroom,
                "scheduled_date": schema.scheduled_date,
            },
        )

        await self.db.flush()
        await self.db.refresh(hearing)

        # Notify assigned judge, lawyer, and citizen
        notif_service = NotificationService(self.db)
        recipients = {case.filed_by, case.assigned_judge, case.assigned_lawyer} - {None}
        for user_id in recipients:
            await notif_service.create_notification(
                NotificationCreateSchema(
                    user_id=user_id,
                    title=f"Hearing Scheduled: {case.case_number}",
                    message=f"Next hearing ({schema.hearing_type}) scheduled on {schema.scheduled_date} in {schema.courtroom}.",
                    notification_type="hearing_alert",
                    link=f"/judge/cases/{case.id}",
                )
            )

        logger.info(
            "Hearing scheduled successfully",
            extra={"case_id": case.id, "hearing_id": hearing.id},
        )
        return HearingScheduleResponseSchema.model_validate(hearing)

    async def get_case_timeline(self, case_id: str) -> CaseTimelineResponseSchema:
        """
        Build complete chronological milestone timeline for a case.
        """
        from app.cases.schemas import CaseTimelineNodeSchema, CaseTimelineResponseSchema
        from app.evidence.models import EvidenceRecord
        from sqlalchemy import select

        case = await self.repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(message=f"Case with ID '{case_id}' not found.")

        timeline_nodes: list[CaseTimelineNodeSchema] = []

        # 1. Case Filing Milestone
        timeline_nodes.append(
            CaseTimelineNodeSchema(
                id=f"filing-{case.id}",
                timestamp=case.created_at.isoformat(),
                milestone_type="FILING",
                title=f"Case Filed: {case.case_number}",
                description=f"Case '{case.title}' filed initially as {case.case_type} with priority {case.priority.upper()}.",
                actor_id=case.filed_by,
                badge_color="bg-blue-500",
                metadata={"case_number": case.case_number, "priority": case.priority},
            )
        )

        # 2. Case Events
        for ev in case.events:
            timeline_nodes.append(
                CaseTimelineNodeSchema(
                    id=ev.id,
                    timestamp=ev.created_at.isoformat(),
                    milestone_type="EVENT",
                    title=ev.event_type.replace("_", " ").title(),
                    description=ev.description or "Case event recorded.",
                    actor_id=ev.performed_by,
                    badge_color="bg-purple-500",
                    metadata=ev.event_data,
                )
            )

        # 3. Evidence Submissions
        ev_stmt = select(EvidenceRecord).where(EvidenceRecord.case_id == case_id)
        ev_res = await self.db.execute(ev_stmt)
        evidence_list = ev_res.scalars().all()
        for e in evidence_list:
            timeline_nodes.append(
                CaseTimelineNodeSchema(
                    id=e.id,
                    timestamp=e.created_at.isoformat(),
                    milestone_type="EVIDENCE",
                    title=f"Evidence Submitted: {e.evidence_type.title()}",
                    description=f"Integrity Status: {e.verification_status.upper()} (Hash: {e.integrity_hash[:12]}...)",
                    actor_id=e.verified_by,
                    badge_color="bg-emerald-500"
                    if e.verification_status == "verified"
                    else "bg-amber-500",
                    metadata={
                        "verification_status": e.verification_status,
                        "hash": e.integrity_hash,
                    },
                )
            )

        # 4. Hearings
        from app.cases.models import HearingSchedule

        h_stmt = select(HearingSchedule).where(HearingSchedule.case_id == case_id)
        h_res = await self.db.execute(h_stmt)
        hearings = h_res.scalars().all()
        for h in hearings:
            timeline_nodes.append(
                CaseTimelineNodeSchema(
                    id=h.id,
                    timestamp=h.created_at.isoformat(),
                    milestone_type="HEARING",
                    title=f"Hearing: {h.hearing_type}",
                    description=f"Scheduled for {h.scheduled_date} in {h.courtroom}. Status: {h.status}.",
                    actor_id=h.scheduled_by,
                    badge_color="bg-indigo-500",
                    metadata={"courtroom": h.courtroom, "status": h.status},
                )
            )

        # Sort timeline chronologically
        timeline_nodes.sort(key=lambda x: x.timestamp)

        return CaseTimelineResponseSchema(
            case_id=case.id,
            case_number=case.case_number,
            total_milestones=len(timeline_nodes),
            timeline=timeline_nodes,
        )
