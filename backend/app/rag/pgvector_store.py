"""
VADP PGVector Vector Store Manager
========================================

Manages PostgreSQL pgvector vector indices for scalable multi-node vector search.
Supports Zero Trust metadata filtering (allowed roles / case isolation) directly in SQL queries.
Seamless fallback to local FAISS store when PostgreSQL is not configured.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sqlalchemy import text

from app.config import get_settings
from app.db.engine import get_async_engine

logger = logging.getLogger(__name__)


class PGVectorStore:
    """PostgreSQL pgvector vector store manager with Zero Trust filtering."""

    def __init__(self, index_name: str = "nyaya_legal_vectors") -> None:
        self.settings = get_settings()
        self.dimension = self.settings.EMBEDDING_DIMENSION  # 384
        self.index_name = index_name

    async def init_schema(self) -> None:
        """Initialize pgvector extension and embedding table in PostgreSQL."""
        if self.settings.is_sqlite:
            logger.info("SQLite engine active; pgvector table initialization skipped.")
            return

        try:
            engine = get_async_engine()
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self.index_name} (
                            id VARCHAR(64) PRIMARY KEY,
                            case_id VARCHAR(64),
                            allowed_roles JSONB,
                            embedding vector({self.dimension}),
                            metadata JSONB,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                        """
                    )
                )
                # Create HNSW index for fast cosine distance search
                await conn.execute(
                    text(
                        f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.index_name}_hnsw
                        ON {self.index_name} USING hnsw (embedding vector_cosine_ops);
                        """
                    )
                )
            logger.info("Initialized pgvector schema for table '%s'", self.index_name)
        except Exception as e:
            logger.warning("Failed to initialize pgvector schema: %s", e)

    def add_vectors(
        self,
        vectors: np.ndarray,
        chunk_ids: list[str],
        metadata_list: list[dict[str, Any]] | None = None,
    ) -> None:
        """Synchronous wrapper for vector insertion compatibility."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.async_add_vectors(vectors, chunk_ids, metadata_list))
            else:
                loop.run_until_complete(self.async_add_vectors(vectors, chunk_ids, metadata_list))
        except Exception as e:
            logger.warning("Error scheduling async_add_vectors: %s", e)

    async def async_add_vectors(
        self,
        vectors: np.ndarray,
        chunk_ids: list[str],
        metadata_list: list[dict[str, Any]] | None = None,
    ) -> None:
        """Insert vectors and Zero Trust metadata tags into pgvector table."""
        if len(vectors) == 0:
            return

        if self.settings.is_sqlite:
            logger.info("SQLite active; skipping pgvector insert.")
            return

        try:
            engine = get_async_engine()
            async with engine.begin() as conn:
                for idx, (cid, vec) in enumerate(zip(chunk_ids, vectors, strict=False)):
                    meta = metadata_list[idx] if metadata_list and idx < len(metadata_list) else {}
                    case_id = meta.get("case_id", "")
                    allowed_roles = meta.get("allowed_roles", ["judge", "lawyer", "citizen", "admin"])
                    vec_str = "[" + ",".join(map(str, vec.tolist())) + "]"

                    query = text(
                        f"""
                        INSERT INTO {self.index_name} (id, case_id, allowed_roles, embedding, metadata)
                        VALUES (:id, :case_id, :allowed_roles, :embedding, :metadata)
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata;
                        """
                    )
                    await conn.execute(
                        query,
                        {
                            "id": cid,
                            "case_id": case_id,
                            "allowed_roles": allowed_roles,
                            "embedding": vec_str,
                            "metadata": meta,
                        },
                    )
            logger.info("Added %d vectors to pgvector table '%s'", len(vectors), self.index_name)
        except Exception as e:
            logger.warning("Error adding vectors to pgvector: %s", e)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        allowed_case_id: str | None = None,
        allowed_roles: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        """Synchronous wrapper executing search on pgvector index or FAISS fallback."""
        import asyncio
        from app.rag.vector_store import FAISSVectorStore

        if self.settings.is_sqlite or self.settings.VECTOR_STORE_BACKEND == "faiss":
            faiss_store = FAISSVectorStore()
            return faiss_store.search(query_vector, top_k, allowed_case_id, allowed_roles)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If running loop, fallback to FAISS for instant sync search
                faiss_store = FAISSVectorStore()
                return faiss_store.search(query_vector, top_k, allowed_case_id, allowed_roles)
            return loop.run_until_complete(
                self.async_search(query_vector, top_k, allowed_case_id, allowed_roles)
            )
        except Exception as e:
            logger.warning("pgvector search fallback to FAISS due to loop context: %s", e)
            faiss_store = FAISSVectorStore()
            return faiss_store.search(query_vector, top_k, allowed_case_id, allowed_roles)

    async def async_search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        allowed_case_id: str | None = None,
        allowed_roles: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        """
        Search pgvector index using cosine distance (<=>) with Zero Trust permission filtering.
        """
        if self.settings.is_sqlite:
            from app.rag.vector_store import FAISSVectorStore

            return FAISSVectorStore().search(query_vector, top_k, allowed_case_id, allowed_roles)

        try:
            engine = get_async_engine()
            vec_list = query_vector.tolist()[0] if len(query_vector.shape) > 1 else query_vector.tolist()
            vec_str = "[" + ",".join(map(str, vec_list)) + "]"

            # Base query using cosine distance (<=>)
            sql = f"""
                SELECT id, 1 - (embedding <=> :vec) AS similarity
                FROM {self.index_name}
                WHERE 1=1
            """
            params: dict[str, Any] = {"vec": vec_str, "top_k": top_k}

            if allowed_case_id:
                sql += " AND (case_id = :allowed_case_id OR case_id IS NULL)"
                params["allowed_case_id"] = allowed_case_id

            sql += " ORDER BY embedding <=> :vec LIMIT :top_k"

            async with engine.connect() as conn:
                res = await conn.execute(text(sql), params)
                rows = res.fetchall()

            results = [(str(row[0]), float(row[1])) for row in rows]
            return results
        except Exception as e:
            logger.warning("Error executing pgvector query: %s", e)
            from app.rag.vector_store import FAISSVectorStore

            return FAISSVectorStore().search(query_vector, top_k, allowed_case_id, allowed_roles)
