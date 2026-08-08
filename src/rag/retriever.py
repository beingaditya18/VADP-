"""
VADP Context Retriever Module
==================================

Retrieves top-k relevant document chunks from FAISS vector store,
filters by similarity threshold, and constructs structured prompt context with legal citations.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.documents.models import Document
from app.rag.embeddings import EmbeddingGenerator
from app.rag.models import DocumentChunk
from app.rag.schemas import CitationSchema
from app.rag.vector_store import FAISSVectorStore


class ContextRetriever:
    """Retriever fetching relevant chunks and building cited prompt context."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.encoder = EmbeddingGenerator()
        self.vector_store = FAISSVectorStore()
        self.settings = get_settings()

    async def retrieve_relevant_context(
        self, query_text: str, case_id: str | None = None, top_k: int = 5
    ) -> tuple[str, list[CitationSchema]]:
        """
        Search FAISS index for relevant chunks, resolve document metadata from SQLite,
        and build prompt context text along with citation list.
        """
        # Encode query to vector
        query_vec = self.encoder.encode([query_text])

        # Vector search
        search_results = self.vector_store.search(query_vec, top_k=top_k * 2)  # Over-fetch for case_id filtering

        if not search_results:
            return "", []

        # Filter by threshold & case_id
        chunk_ids = [chunk_id for chunk_id, score in search_results if score >= self.settings.RAG_SIMILARITY_THRESHOLD]
        score_map = {chunk_id: score for chunk_id, score in search_results}

        if not chunk_ids:
            return "", []

        # Fetch Chunk records from DB
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.id.in_(chunk_ids))
        )
        db_results = await self.db.execute(stmt)
        chunks = db_results.scalars().all()

        # Fetch Document metadata
        doc_ids = list({c.document_id for c in chunks})
        doc_stmt = select(Document).where(Document.id.in_(doc_ids))
        doc_results = await self.db.execute(doc_stmt)
        doc_map = {d.id: d for d in doc_results.scalars().all()}

        # Filter by case_id if specified
        filtered_chunks = []
        for chunk in chunks:
            doc = doc_map.get(chunk.document_id)
            if doc:
                if case_id and doc.case_id != case_id:
                    continue
                filtered_chunks.append((chunk, doc))

        filtered_chunks = filtered_chunks[:top_k]

        if not filtered_chunks:
            return "", []

        # Build context prompt & citations
        context_parts = []
        citations = []

        for idx, (chunk, doc) in enumerate(filtered_chunks, start=1):
            score = score_map.get(chunk.id, 0.0)
            context_parts.append(
                f"[Source Citation #{idx} | Document: {doc.file_name} | Chunk #{chunk.chunk_index}]\n{chunk.content}"
            )
            citations.append(
                CitationSchema(
                    document_id=doc.id,
                    file_name=doc.file_name,
                    chunk_index=chunk.chunk_index,
                    relevance_score=round(score, 3),
                    excerpt=chunk.content[:200] + "...",
                )
            )

        full_context = "\n\n---\n\n".join(context_parts)
        return full_context, citations
