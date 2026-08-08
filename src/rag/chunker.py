"""
VADP Text Chunker Module
=============================

Splits document text into semantic chunks using sliding windows with token overlap.
Default chunk size: 512 tokens (~2000 chars), overlap: 50 tokens (~200 chars).
"""

from __future__ import annotations

import re


class TextChunker:
    """Sliding-window document chunker."""

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size_chars: int = 1500,
        overlap_chars: int = 200,
    ) -> list[str]:
        """
        Split raw document text into overlapping text chunks.
        Strips extra whitespace while preserving paragraph boundaries.
        """
        if not text or not text.strip():
            return []

        # Normalize newlines
        cleaned_text = re.sub(r"\r\n|\r", "\n", text.strip())

        if len(cleaned_text) <= chunk_size_chars:
            return [cleaned_text]

        chunks = []
        start = 0
        text_length = len(cleaned_text)

        while start < text_length:
            end = start + chunk_size_chars

            if end < text_length:
                # Find last sentence boundary (. \n) near end to prevent cutting sentences in half
                boundary = max(
                    cleaned_text.rfind(". ", start, end),
                    cleaned_text.rfind("\n", start, end),
                )
                if boundary != -1 and boundary > start + (chunk_size_chars // 2):
                    end = boundary + 1

            chunk_str = cleaned_text[start:end].strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Move window with overlap
            start = end - overlap_chars if (end - overlap_chars) > start else end

        return chunks
