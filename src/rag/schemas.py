"""
VADP RAG Schemas
=====================

Pydantic schemas for RAG queries, chunks, context building, and legal citations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CitationSchema(BaseModel):
    document_id: str
    file_name: str
    chunk_index: int
    relevance_score: float
    excerpt: str


class RAGQueryRequestSchema(BaseModel):
    query_text: str = Field(..., min_length=3, max_length=2000, description="Legal search question or prompt")
    case_id: str | None = Field(default=None, description="Optional case scope filter")
    top_k: int = Field(default=5, ge=1, le=20)


class RAGQueryResponseSchema(BaseModel):
    query: str
    answer: str
    citations: list[CitationSchema]
    processing_time_ms: int
    case_id: str | None = None
    created_at: datetime
    retrieval_metadata: dict[str, Any] | None = Field(
        default=None,
        description="VADP: RAG retrieval pipeline metadata for reproducibility",
    )


class DocumentChunkResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int | None = None
    created_at: datetime
