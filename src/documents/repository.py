"""
VADP Document Repository
=============================

Data access layer for Document model.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document


class DocumentRepository:
    """Repository implementation for Document operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def create_document(self, doc: Document) -> Document:
        """Store document metadata record."""
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def get_by_id(self, doc_id: str) -> Document | None:
        """Fetch document by primary key ID."""
        result = await self.db.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    async def list_by_case(self, case_id: str) -> Sequence[Document]:
        """Fetch all documents attached to a specific case."""
        result = await self.db.execute(
            select(Document)
            .where(Document.case_id == case_id)
            .order_by(Document.created_at.desc())
        )
        return result.scalars().all()

    async def delete_document(self, doc_id: str) -> bool:
        """Delete document metadata record."""
        doc = await self.get_by_id(doc_id)
        if not doc:
            return False
        await self.db.delete(doc)
        await self.db.flush()
        return True
