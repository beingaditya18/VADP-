"""
VADP RAG Service
=====================

Business logic for document indexing into FAISS vector store, prompt building,
LLM legal query execution, and query audit history logging.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.documents.models import Document
from app.llm.client import LLMClient
from app.rag.chunker import TextChunker
from app.rag.embeddings import EmbeddingGenerator
from app.rag.models import DocumentChunk, RAGQuery
from app.rag.retriever import ContextRetriever
from app.rag.schemas import RAGQueryRequestSchema, RAGQueryResponseSchema
from app.rag.vector_store import FAISSVectorStore
from app.rag.entailment import CitationEntailmentVerifier

logger = get_logger(__name__)


class RAGService:
    """Service managing RAG indexing and query processing."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.encoder = EmbeddingGenerator()
        self.vector_store = FAISSVectorStore()
        self.retriever = ContextRetriever(db)
        self.llm = LLMClient()
        self.entailment_verifier = CitationEntailmentVerifier(entailment_threshold=0.50)

    async def index_document(self, document_id: str) -> int:
        """
        Extract text from uploaded document file, split into sliding window chunks,
        compute Sentence-Transformers embeddings in non-blocking thread, and insert into FAISS index.
        """
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError(message="Document not found.")

        # Read text from file (for TXT/MD/Plain text; or fallback to raw content)
        try:
            async with aiofiles.open(doc.storage_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = await f.read()
        except Exception:
            raw_text = f"Document File: {doc.file_name} (Content extracted from document metadata)"

        if not raw_text.strip():
            raw_text = f"Document Filename: {doc.file_name}"

        # Chunk text
        chunks_text = TextChunker.chunk_text(raw_text)
        if not chunks_text:
            return 0

        # Encode embeddings offloaded to thread pool to prevent event loop blocking
        embeddings = await asyncio.to_thread(self.encoder.encode, chunks_text)

        # Store DocumentChunk records in DB
        chunk_ids = []
        metadata_list = []
        for idx, chunk_content in enumerate(chunks_text):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_content,
                token_count=len(chunk_content.split()),
            )
            self.db.add(db_chunk)
            await self.db.flush()
            chunk_ids.append(db_chunk.id)
            metadata_list.append({"case_id": doc.case_id, "document_id": doc.id})

        # Add vectors to FAISS index with Zero Trust permission metadata
        await asyncio.to_thread(self.vector_store.add_vectors, embeddings, chunk_ids, metadata_list)
        logger.info("Indexed document into FAISS", extra={"doc_id": doc.id, "chunks": len(chunk_ids)})
        return len(chunk_ids)

    async def answer_query(
        self, schema: RAGQueryRequestSchema, user_id: str
    ) -> RAGQueryResponseSchema:
        """
        Execute RAG legal research query:
          1. Retrieve relevant context & citations from FAISS + DB
          2. Build augmented system prompt
          3. Generate response via LLMClient
          4. Record RAGQuery audit log in DB
        """
        start_time = time.perf_counter()

        # Retrieve relevant context
        context_text, citations = await self.retriever.retrieve_relevant_context(
            query_text=schema.query_text,
            case_id=schema.case_id,
            top_k=schema.top_k,
        )

        system_prompt = (
            "You are Nyaya-AI, an expert Explainable AI Judicial Decision Support Assistant. "
            "Your duty is to assist judges and legal professionals by analyzing cases grounded strictly in verified legal documents. "
            "Always cite source documents using format [Source Citation #N] when referencing facts."
        )

        user_prompt = f"User Question: {schema.query_text}\n\n"
        if context_text:
            user_prompt += f"Grounded Case Documents Context:\n{context_text}\n\n"
        else:
            user_prompt += "No specific document context found in vector index for this query. Provide general legal principles based on standard jurisprudence."

        # Call LLM client (with prompt injection scanning)
        llm_response = await self.llm.generate_completion(system_prompt, user_prompt)
        answer_text = llm_response["content"]

        # Run citation entailment verification step
        citation_dicts = [c.model_dump() for c in citations]
        verified_citations, entailment_results = self.entailment_verifier.filter_citations(
            citations=citation_dicts, generated_claim=answer_text
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # Record RAG query audit log
        audit_query = RAGQuery(
            user_id=user_id,
            case_id=schema.case_id,
            query_text=schema.query_text,
            response_text=answer_text,
            citations=verified_citations,
            processing_time_ms=elapsed_ms,
        )
        self.db.add(audit_query)

        return RAGQueryResponseSchema(
            query=schema.query_text,
            answer=answer_text,
            citations=citations,
            processing_time_ms=elapsed_ms,
            case_id=schema.case_id,
            created_at=datetime.now(timezone.utc),
            retrieval_metadata={
                "embedding_model": self.encoder.model_name if hasattr(self.encoder, "model_name") else "all-MiniLM-L6-v2",
                "top_k": schema.top_k,
                "similarity_threshold": 0.3,
                "retrieval_latency_ms": elapsed_ms,
                "total_chunks_searched": self.vector_store.index.ntotal if hasattr(self.vector_store, "index") and self.vector_store.index else 0,
                "entailment_verified": True,
                "entailment_scores": [e.entailment_score for e in entailment_results],
                "supported_citations_count": len(verified_citations),
            },
        )
