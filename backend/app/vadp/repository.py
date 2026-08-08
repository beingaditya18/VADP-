"""
VADP VADP Repository
=========================

Data access layer for Verification Contracts and Contract Events.
Follows the existing repository pattern established in app.ledger.repository
and app.cases.repository.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.vadp.models import ContractEvent, VerificationContract

logger = get_logger(__name__)


class VerificationContractRepository:
    """Data access for Verification Contracts and Contract Events."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Contract CRUD ────────────────────────────────────────

    async def create_contract(
        self, contract: VerificationContract,
    ) -> VerificationContract:
        """Persist a new Verification Contract to the database."""
        self.db.add(contract)
        await self.db.flush()
        await self.db.refresh(contract, attribute_names=["events"])
        logger.info(
            "Created verification contract",
            extra={"contract_id": contract.id, "case_id": contract.case_id},
        )
        return contract

    async def get_contract_by_id(
        self, contract_id: str,
    ) -> VerificationContract | None:
        """Fetch a contract by its primary key, including events."""
        stmt = (
            select(VerificationContract)
            .where(VerificationContract.id == contract_id)
            .options(selectinload(VerificationContract.events))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_contract_by_recommendation(
        self, recommendation_id: str,
    ) -> VerificationContract | None:
        """Fetch the contract bound to a specific AI recommendation."""
        stmt = (
            select(VerificationContract)
            .where(VerificationContract.recommendation_id == recommendation_id)
            .options(selectinload(VerificationContract.events))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_contracts_for_case(
        self, case_id: str,
    ) -> list[VerificationContract]:
        """Fetch all contracts associated with a case, newest first. Accepts Case ID or Case Number."""
        from app.cases.models import Case
        # 1. Direct match on VerificationContract.case_id
        stmt = (
            select(VerificationContract)
            .where(VerificationContract.case_id == case_id)
            .options(selectinload(VerificationContract.events))
            .order_by(VerificationContract.generated_at.desc())
        )
        result = await self.db.execute(stmt)
        contracts = list(result.scalars().all())
        if contracts:
            return contracts

        # 2. Match by querying Case by case_number or id
        case_stmt = select(Case).where((Case.case_number == case_id) | (Case.id == case_id))
        case_res = await self.db.execute(case_stmt)
        c_obj = case_res.scalar_one_or_none()
        if c_obj:
            stmt = (
                select(VerificationContract)
                .where((VerificationContract.case_id == c_obj.id) | (VerificationContract.case_id == c_obj.case_number))
                .options(selectinload(VerificationContract.events))
                .order_by(VerificationContract.generated_at.desc())
            )
            result = await self.db.execute(stmt)
            contracts = list(result.scalars().all())

        return contracts

    async def update_contract(
        self, contract: VerificationContract,
    ) -> VerificationContract:
        """Persist updates to an existing contract."""
        await self.db.flush()
        await self.db.refresh(contract, attribute_names=["events"])
        return contract

    async def list_contracts(
        self,
        page: int = 1,
        page_size: int = 20,
        completeness_filter: str | None = None,
        review_filter: str | None = None,
    ) -> tuple[list[VerificationContract], int]:
        """
        Paginated listing of all Verification Contracts with optional filters.

        Returns (contracts, total_count).
        """
        base_query = select(VerificationContract)

        if completeness_filter:
            base_query = base_query.where(
                VerificationContract.completeness_status == completeness_filter
            )
        if review_filter:
            base_query = base_query.where(
                VerificationContract.human_review_status == review_filter
            )

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        data_stmt = (
            base_query
            .options(selectinload(VerificationContract.events))
            .order_by(VerificationContract.generated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(data_stmt)
        contracts = list(result.scalars().all())

        return contracts, total

    # ── Contract Event CRUD ──────────────────────────────────

    async def add_event(self, event: ContractEvent) -> ContractEvent:
        """Persist a new contract event to the database."""
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_events_for_contract(
        self, contract_id: str,
    ) -> list[ContractEvent]:
        """Fetch all events for a contract, ordered by event_order."""
        stmt = (
            select(ContractEvent)
            .where(ContractEvent.contract_id == contract_id)
            .order_by(ContractEvent.event_order.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_event(
        self, contract_id: str,
    ) -> ContractEvent | None:
        """Fetch the most recent event for a contract."""
        stmt = (
            select(ContractEvent)
            .where(ContractEvent.contract_id == contract_id)
            .order_by(ContractEvent.event_order.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_human_override_coverage(self) -> dict[str, Any]:
        """
        Calculate aggregate Human Override Coverage metric across all contracts.
        """
        total_stmt = select(func.count(VerificationContract.id))
        total_res = await self.db.execute(total_stmt)
        total = total_res.scalar() or 0

        reviewed_stmt = select(func.count(VerificationContract.id)).where(
            VerificationContract.human_review_status != "pending_review"
        )
        reviewed_res = await self.db.execute(reviewed_stmt)
        reviewed = reviewed_res.scalar() or 0

        approved_stmt = select(func.count(VerificationContract.id)).where(
            VerificationContract.human_review_status == "approved"
        )
        approved_res = await self.db.execute(approved_stmt)
        approved = approved_res.scalar() or 0

        rejected_stmt = select(func.count(VerificationContract.id)).where(
            VerificationContract.human_review_status.in_(["rejected", "override"])
        )
        rejected_res = await self.db.execute(rejected_stmt)
        rejected = rejected_res.scalar() or 0

        flagged_stmt = select(func.count(VerificationContract.id)).where(
            VerificationContract.human_review_status == "flagged"
        )
        flagged_res = await self.db.execute(flagged_stmt)
        flagged = flagged_res.scalar() or 0

        pending = max(0, total - reviewed)
        coverage_pct = round((reviewed / total * 100.0), 2) if total > 0 else 100.0

        return {
            "total_contracts": total,
            "reviewed_contracts": reviewed,
            "approved_count": approved,
            "rejected_override_count": rejected,
            "flagged_count": flagged,
            "pending_count": pending,
            "human_override_coverage_pct": coverage_pct,
            "review_action_breakdown": {
                "approved": approved,
                "rejected_override": rejected,
                "flagged": flagged,
                "pending": pending,
            },
        }

