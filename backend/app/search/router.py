"""
Nyaya-ZTA Search Router
=======================

REST API endpoint for hybrid keyword + vector semantic search:
  - GET /api/v1/search?q=...
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.search.service import HybridSearchResponseSchema, SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=HybridSearchResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Execute hybrid search",
    description="Search cases, documents, and FAISS vector indices using keyword and semantic similarity search.",
)
async def hybrid_search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query string"),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> HybridSearchResponseSchema:
    service = SearchService(db)
    return await service.execute_hybrid_search(q, limit=limit)
