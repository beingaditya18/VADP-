"""
VADP Text Embeddings Generator
====================================

Generates 384-dimensional dense vector embeddings using Sentence-Transformers (all-MiniLM-L6-v2).
Provides normalized fallback encoder for fast testing environments.
"""

from __future__ import annotations

import hashlib
import numpy as np

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_model_instance = None


class EmbeddingGenerator:
    """Sentence embedding generator."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.dimension = self.settings.EMBEDDING_DIMENSION  # 384

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Encode a list of text strings into a float32 numpy array of shape (N, 384).
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        global _model_instance

        # Attempt Sentence-Transformers loading if available
        if not self.settings.is_testing:
            try:
                if _model_instance is None:
                    from sentence_transformers import SentenceTransformer
                    _model_instance = SentenceTransformer(self.settings.EMBEDDING_MODEL)
                    logger.info("Loaded SentenceTransformer model: %s", self.settings.EMBEDDING_MODEL)

                embeddings = _model_instance.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.astype(np.float32)
            except Exception as e:
                logger.warning("Falling back to feature vector generator: %s", str(e))

        # Fallback: Deterministic normalized pseudo-embeddings for testing / fast offline execution
        vectors = []
        for text in texts:
            vec = self._fallback_encode_single(text)
            vectors.append(vec)

        return np.array(vectors, dtype=np.float32)

    def _fallback_encode_single(self, text: str) -> np.ndarray:
        """Generate deterministic 384-dim normalized vector from PBKDF2 bytes."""
        # 384 float32 floats require 384 * 4 = 1536 bytes
        key_bytes = hashlib.pbkdf2_hmac("sha256", text.encode("utf-8"), b"nyaya_vector_salt", iterations=1, dklen=1536)
        raw = np.frombuffer(key_bytes, dtype=np.float32)
        norm = np.linalg.norm(raw)
        if norm > 0:
            raw = raw / norm
        return raw
