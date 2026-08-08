"""
Okapi BM25 Lexical Retrieval Engine for Legal Documents.

Serves as the standard lexical baseline (rank_bm25 / Elasticsearch model)
for legal retrieval evaluation.
"""

from typing import List, Dict, Any, Tuple
import math
import numpy as np
from collections import Counter
from pydantic import BaseModel


class BM25ChunkScore(BaseModel):
    chunk_id: str
    bm25_score: float
    rank: int
    snippet: str


class BM25Retriever:
    """
    Okapi BM25 Lexical Retriever.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len: List[int] = []
        self.avgdl: float = 0.0
        self.doc_freqs: List[Counter] = []
        self.idf: Dict[str, float] = {}
        self.chunks: List[Dict[str, Any]] = []

    def fit(self, chunks: List[Dict[str, Any]]) -> None:
        """Indexes candidate chunks and precomputes corpus IDF stats."""
        self.chunks = chunks
        self.doc_len = []
        self.doc_freqs = []
        df: Counter = Counter()

        for chunk in chunks:
            text = str(chunk.get("content", chunk.get("snippet", ""))).lower()
            tokens = text.split()
            self.doc_len.append(len(tokens))
            counts = Counter(tokens)
            self.doc_freqs.append(counts)
            for t in counts:
                df[t] += 1

        self.avgdl = float(np.mean(self.doc_len)) if self.doc_len else 1.0
        n_docs = len(chunks)

        for term, freq in df.items():
            # Standard Okapi BM25 IDF formula
            self.idf[term] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query_text: str, top_k: int = 5) -> List[BM25ChunkScore]:
        """Performs Okapi BM25 search over indexed chunks."""
        q_tokens = query_text.lower().split()
        scores = []

        for idx, (counts, dlen) in enumerate(zip(self.doc_freqs, self.doc_len)):
            score = 0.0
            for t in q_tokens:
                if t in counts:
                    freq = counts[t]
                    idf_val = self.idf.get(t, 0.0)
                    denom = freq + self.k1 * (
                        1.0 - self.b + self.b * (dlen / self.avgdl)
                    )
                    score += idf_val * (freq * (self.k1 + 1.0)) / denom

            chunk_id = str(
                self.chunks[idx].get(
                    "id", self.chunks[idx].get("chunk_id", f"chk_{idx}")
                )
            )
            snippet = str(
                self.chunks[idx].get("content", self.chunks[idx].get("snippet", ""))
            )
            scores.append((chunk_id, float(round(score, 4)), snippet))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank_idx, (cid, sval, snip) in enumerate(scores[:top_k]):
            results.append(
                BM25ChunkScore(
                    chunk_id=cid, bm25_score=sval, rank=rank_idx + 1, snippet=snip
                )
            )

        return results
