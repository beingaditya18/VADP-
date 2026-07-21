"""
Unit & Integration tests for RAG Pipeline (Chunking, Vector Store, Citations API).
"""

from __future__ import annotations

import io
import pytest
from httpx import AsyncClient

from app.rag.chunker import TextChunker


class TestTextChunker:
    """Unit test suite for text chunking."""

    def test_chunking_short_text(self) -> None:
        text = "This is a short sentence."
        chunks = TextChunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunking_long_text_sliding_window(self) -> None:
        text = "Sentence one. " * 200
        chunks = TextChunker.chunk_text(text, chunk_size_chars=500, overlap_chars=50)
        assert len(chunks) > 1


@pytest.mark.asyncio
class TestRAGAPI:
    """Integration test suite for RAG indexing & query endpoints."""

    async def test_rag_indexing_and_query_flow(self, async_client: AsyncClient) -> None:
        # 1. Register Lawyer & File Case
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "lawyer.advocate@nyaya.in",
                "password": "Password123!",
                "full_name": "Advocate Legal",
                "role": "lawyer",
                "bar_number": "DEL/100/2022",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        case_res = await async_client.post(
            "/api/v1/cases",
            json={"title": "Land Acquisition Appeal", "case_type": "Civil"},
            headers=headers,
        )
        case_id = case_res.json()["id"]

        # 2. Upload Document
        doc_text = b"Section 100 of the Civil Procedure Code governs second appeals. In land acquisition cases, natural justice principles apply strictly."
        files = {"file": ("statute_brief.txt", io.BytesIO(doc_text), "text/plain")}

        upload_res = await async_client.post(
            f"/api/v1/documents/upload/{case_id}",
            files=files,
            headers=headers,
        )
        doc_id = upload_res.json()["id"]

        # 3. Index Document for RAG
        index_res = await async_client.post(f"/api/v1/rag/index/{doc_id}", headers=headers)
        assert index_res.status_code == 200
        assert index_res.json()["chunks_indexed"] > 0

        # 4. Query RAG Legal Assistant
        query_res = await async_client.post(
            "/api/v1/rag/query",
            json={
                "query_text": "What principles apply to land acquisition second appeals under Section 100?",
                "case_id": case_id,
            },
            headers=headers,
        )
        assert query_res.status_code == 200
        rag_data = query_res.json()
        assert "answer" in rag_data
        assert "citations" in rag_data
