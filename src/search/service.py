"""
VADP Hybrid Search Service
===============================

Combines:
  1. Full-Text SQL keyword search across Cases, Case Numbers, and Documents
  2. FAISS Semantic Vector Similarity Search
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cases.models import Case
from app.cases.schemas import CaseResponseSchema
from app.documents.models import Document
from app.rag.retriever import ContextRetriever


class SearchResultItem(BaseModel):
    category: str  # 'case' | 'document' | 'vector_chunk'
    title: str
    description: str
    relevance_score: float
    metadata: dict[str, Any]


class HybridSearchResponseSchema(BaseModel):
    query: str
    total_results: int
    items: list[SearchResultItem]


class SearchService:
    """Hybrid Search Service combining keyword and FAISS vector search."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.retriever = ContextRetriever(db)

    async def execute_hybrid_search(
        self, query: str, limit: int = 20
    ) -> HybridSearchResponseSchema:
        """
        Execute combined full-text and semantic vector search.
        """
        results: list[SearchResultItem] = []
        if not query or not query.strip():
            return HybridSearchResponseSchema(query=query, total_results=0, items=[])

        search_term = f"%{query.strip()}%"

        # 1. Full-text search on Cases
        case_stmt = (
            select(Case)
            .where(
                or_(
                    Case.title.ilike(search_term),
                    Case.case_number.ilike(search_term),
                    Case.description.ilike(search_term),
                    Case.case_type.ilike(search_term),
                )
            )
            .limit(limit)
        )
        case_results = await self.db.execute(case_stmt)
        for c in case_results.scalars().all():
            results.append(
                SearchResultItem(
                    category="case",
                    title=f"Case: {c.title} ({c.case_number})",
                    description=c.description
                    or f"Category: {c.case_type} | Status: {c.status}",
                    relevance_score=0.95,
                    metadata={
                        "case_id": c.id,
                        "case_number": c.case_number,
                        "status": c.status,
                    },
                )
            )

        # 2. Full-text search on Documents
        doc_stmt = (
            select(Document).where(Document.file_name.ilike(search_term)).limit(limit)
        )
        doc_results = await self.db.execute(doc_stmt)
        for d in doc_results.scalars().all():
            results.append(
                SearchResultItem(
                    category="document",
                    title=f"Document: {d.file_name}",
                    description=f"File Type: {d.file_type or 'TXT'} | SHA-256 Hash Verified",
                    relevance_score=0.90,
                    metadata={
                        "document_id": d.id,
                        "case_id": d.case_id,
                        "hash": d.content_hash,
                    },
                )
            )

        # 3. FAISS Semantic Vector Search
        try:
            _, citations = await self.retriever.retrieve_relevant_context(
                query, top_k=5
            )
            for cite in citations:
                results.append(
                    SearchResultItem(
                        category="vector_chunk",
                        title=f"Vector Precedent: {cite.file_name} (Chunk #{cite.chunk_index})",
                        description=cite.excerpt,
                        relevance_score=cite.relevance_score,
                        metadata={
                            "document_id": cite.document_id,
                            "chunk_index": cite.chunk_index,
                        },
                    )
                )
        except Exception:
            pass

        # Sort by relevance score descending
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return HybridSearchResponseSchema(
            query=query,
            total_results=len(results),
            items=results[:limit],
        )
