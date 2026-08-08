"""
VADP Audit Ledger Repository
=================================

Data access layer for LedgerBlock and LedgerEntry entities using SQLAlchemy 2.x async API.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ledger.models import LedgerBlock, LedgerEntry


class LedgerRepository:
    """Repository pattern for audit ledger operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create_entry(self, entry: LedgerEntry) -> LedgerEntry:
        """Record a new unblocked audit entry."""
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def get_unblocked_entries(self, limit: int = 100) -> Sequence[LedgerEntry]:
        """Fetch audit entries that have not yet been sealed into a block (block_id IS NULL)."""
        result = await self.db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.block_id.is_(None))
            .order_by(LedgerEntry.timestamp.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create_block(
        self, block: LedgerBlock, entries: list[LedgerEntry]
    ) -> LedgerBlock:
        """Seal a list of entries into a new immutable LedgerBlock."""
        self.db.add(block)
        await self.db.flush()

        for entry in entries:
            entry.block_id = block.id

        await self.db.flush()
        return await self.get_block_by_index(
            block.block_index
        )  # Preloaded with entries

    async def get_latest_block(self) -> LedgerBlock | None:
        """Fetch tip block of the hash chain (highest index)."""
        result = await self.db.execute(
            select(LedgerBlock)
            .order_by(LedgerBlock.block_index.desc())
            .limit(1)
            .options(selectinload(LedgerBlock.entries))
        )
        return result.scalar_one_or_none()

    async def get_block_by_index(self, index: int) -> LedgerBlock | None:
        """Fetch block by block_index."""
        result = await self.db.execute(
            select(LedgerBlock)
            .where(LedgerBlock.block_index == index)
            .options(selectinload(LedgerBlock.entries))
        )
        return result.scalar_one_or_none()

    async def get_all_blocks(self) -> Sequence[LedgerBlock]:
        """Fetch all blocks in chronological order."""
        result = await self.db.execute(
            select(LedgerBlock)
            .order_by(LedgerBlock.block_index.asc())
            .options(selectinload(LedgerBlock.entries))
        )
        return result.scalars().all()

    async def get_entry_by_id(self, entry_id: str) -> LedgerEntry | None:
        """Fetch entry by ID with block and block.entries preloaded."""
        result = await self.db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.id == entry_id)
            .options(selectinload(LedgerEntry.block).selectinload(LedgerBlock.entries))
        )
        return result.scalar_one_or_none()
