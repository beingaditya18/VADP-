"""
Nyaya-ZTA RAG Router
====================

REST API endpoints for Retrieval-Augmented Generation:
  - POST /api/v1/rag/index/{document_id}
  - POST /api/v1/rag/query
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.db.session import get_db_session
from app.rag.schemas import RAGQueryRequestSchema, RAGQueryResponseSchema
from app.rag.service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post(
    "/index/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Index document for RAG search",
    description="Chunk text from an uploaded document, generate embeddings, and insert into FAISS vector index.",
)
async def index_document(
    document_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    service = RAGService(db)
    chunks_indexed = await service.index_document(document_id)
    return {"message": "Document indexed successfully", "document_id": document_id, "chunks_indexed": chunks_indexed}


@router.post(
    "/query",
    response_model=RAGQueryResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Ask legal research query",
    description="Execute RAG search against vector store and generate grounded LLM legal research answer with citations.",
)
async def ask_rag_query(
    schema: RAGQueryRequestSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RAGQueryResponseSchema:
    service = RAGService(db)
    return await service.answer_query(schema, current_user.id)
