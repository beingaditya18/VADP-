"""
Nyaya-ZTA FAISS Vector Store Manager
====================================

Manages local FAISS IndexFlatIP (Inner Product cosine similarity) vector indices.
Supports Zero Trust metadata tagging (allowed roles / case isolation) and permission-aware vector filtering.
Persists indices to /backend/faiss_indices/ directory.
"""

from __future__ import annotations

import json
from pathlib import Path
import faiss
import numpy as np

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FAISSVectorStore:
    """Zero Trust permission-aware FAISS vector store manager."""

    def __init__(self, index_name: str = "nyaya_legal_index") -> None:
        self.settings = get_settings()
        self.dimension = self.settings.EMBEDDING_DIMENSION  # 384
        self.index_name = index_name

        self.index_dir = Path(self.settings.FAISS_INDEX_PATH)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_dir / f"{index_name}.index"
        self.id_map_file = self.index_dir / f"{index_name}_id_map.npy"
        self.meta_map_file = self.index_dir / f"{index_name}_meta_map.json"

        self.index: faiss.IndexFlatIP = self._load_or_create_index()
        self.id_map: list[str] = self._load_id_map()
        self.meta_map: dict[str, dict[str, Any]] = self._load_meta_map()

    def _load_or_create_index(self) -> faiss.IndexFlatIP:
        """Load index from disk or create a fresh IndexFlatIP."""
        if self.index_file.exists():
            try:
                idx = faiss.read_index(str(self.index_file))
                logger.info("Loaded FAISS index from disk", extra={"path": str(self.index_file)})
                return idx
            except Exception as e:
                logger.warning("Failed to load FAISS index from disk, recreating: %s", str(e))

        logger.info("Created new FAISS IndexFlatIP (dim=%d)", self.dimension)
        return faiss.IndexFlatIP(self.dimension)

    def _load_id_map(self) -> list[str]:
        """Load mapping of FAISS vector indices to chunk UUID strings."""
        if self.id_map_file.exists():
            try:
                arr = np.load(str(self.id_map_file))
                return arr.tolist()
            except Exception:
                pass
        return []

    def _load_meta_map(self) -> dict[str, dict[str, Any]]:
        """Load permission metadata mapping for chunk UUIDs."""
        if self.meta_map_file.exists():
            try:
                return json.loads(self.meta_map_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def save(self) -> None:
        """Persist FAISS index and metadata maps to disk."""
        faiss.write_index(self.index, str(self.index_file))
        np.save(str(self.id_map_file), np.array(self.id_map))
        self.meta_map_file.write_text(json.dumps(self.meta_map, indent=2), encoding="utf-8")
        logger.info("Saved FAISS index to disk (%d vectors)", self.index.ntotal)

    def add_vectors(
        self,
        vectors: np.ndarray,
        chunk_ids: list[str],
        metadata_list: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Add normalized vectors, chunk IDs, and Zero Trust metadata tags to FAISS index.
        """
        if len(vectors) == 0:
            return

        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.id_map.extend(chunk_ids)

        if metadata_list:
            for cid, meta in zip(chunk_ids, metadata_list, strict=False):
                self.meta_map[cid] = meta

        self.save()

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        allowed_case_id: str | None = None,
        allowed_roles: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        """
        Search FAISS index for top_k most similar vectors with Zero Trust metadata filtering.

        Returns list of tuples: [(chunk_id, similarity_score)]
        """
        if self.index.ntotal == 0:
            return []

        faiss.normalize_L2(query_vector)
        # Fetch candidate set larger than top_k for permission filtering
        candidate_k = min(max(top_k * 4, 20), self.index.ntotal)
        scores, indices = self.index.search(query_vector, candidate_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.id_map):
                chunk_id = self.id_map[idx]
                meta = self.meta_map.get(chunk_id, {})

                # Check case permission boundary if specified
                if allowed_case_id and meta.get("case_id"):
                    if meta["case_id"] != allowed_case_id:
                        continue

                # Check role permission boundary if specified
                if allowed_roles and meta.get("allowed_roles"):
                    if not any(r in meta["allowed_roles"] for r in allowed_roles):
                        continue

                results.append((chunk_id, float(score)))
                if len(results) >= top_k:
                    break

        return results

