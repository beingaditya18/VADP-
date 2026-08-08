"""
Learning-to-Rank (LTR) Engine for VADP RAG Pipeline — Phase 1 Upgrade.
=======================================================================

CHANGES FROM ORIGINAL:
  - Removed static hardcoded feature_weights ([0.25, 0.20, ...])
  - Added SemanticPrecedentRelator: computes dynamic Sim(Q, Cj) × StatutoryMatch(Q, Cj)
  - StatutoryMatch uses Jaccard intersection of statutory section sets
  - Combined score binds to Verification Contract Field 3 (dense_sim) and Field 4 (statutory_match)
  - LambdaMART now falls back to the dynamic combined score when model is untrained

Field Binding:
  Field 3: rag_retrieval_metadata.semantic_similarity   → Sim(Q, Cj)
  Field 4: rag_retrieval_metadata.statutory_match_score → StatutoryMatch(Q, Cj) × Sim(Q, Cj)

Feature Engineering Vector (8 Rich IR Features):
  1. Dense Embedding Cosine Similarity (S_dense)         ← Sim(Q, Cj)
  2. BM25 Lexical Matching Score (S_BM25)
  3. Statutory Section Intersection Score (StatutoryMatch) ← NEW dynamic score
  4. Combined Sim × StatutoryMatch (VADP Field 4)        ← NEW combined score
  5. Temporal Recency Decay (T_decay)
  6. Bench / Coram Relevance (R_bench)
  7. BSA Section 63(4) Evidence Alignment (E_BSA)
  8. Citation Graph PageRank Centrality (C_graph)
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
from pydantic import BaseModel


# ── Semantic Precedent Relator ───────────────────────────────────────────────


class SemanticPrecedentRelator:
    """
    Computes the dynamic two-factor relevance score for the Semantic Precedent Relator.

    Score = Sim(Q, Cj) × StatutoryMatch(Q, Cj)

    Where:
      Sim(Q, Cj)             = dense cosine similarity (from FAISS/sentence-transformers)
      StatutoryMatch(Q, Cj)  = Jaccard overlap of statutory section sets

    This replaces the static manual feature weights from the original implementation.
    Binds to Verification Contract Field 3 (Sim) and Field 4 (combined score).
    """

    # Common section name normalisation patterns
    _SECTION_PATTERN = re.compile(
        r"(?:section|sec\.|art(?:icle)?\.?|order|rule)\s*(\d+[A-Z]?(?:\([a-z0-9]+\))?)",
        re.IGNORECASE,
    )

    @staticmethod
    def normalize_section(section_str: str) -> str:
        """Lowercase and strip whitespace for consistent comparison."""
        return section_str.lower().strip()

    @classmethod
    def extract_section_tokens(cls, sections: list[str]) -> set[str]:
        """
        Convert a list of section strings to a normalized token set.

        E.g. ["Section 65B", "Information Technology Act, 2000"]
             → {"section 65b", "information technology act, 2000", "65b"}
        """
        tokens: set[str] = set()
        for s in sections:
            tokens.add(cls.normalize_section(s))
            # Also extract bare section numbers for fuzzy matching
            for m in cls._SECTION_PATTERN.finditer(s):
                tokens.add(f"sec_{m.group(1).lower()}")
        return tokens

    @classmethod
    def compute_statutory_match(
        cls,
        query_sections: list[str],
        candidate_sections: list[str],
    ) -> float:
        """
        Compute StatutoryMatch(Q, Cj) — Jaccard coefficient of normalized statutory section sets.

        Returns:
            float in [0.0, 1.0]:
              0.0 = no statutory overlap
              1.0 = identical section sets
        """
        if not query_sections or not candidate_sections:
            # If either side has no sections, return a small non-zero prior
            return 0.05

        q_tokens = cls.extract_section_tokens(query_sections)
        c_tokens = cls.extract_section_tokens(candidate_sections)

        intersection = q_tokens & c_tokens
        union = q_tokens | c_tokens

        if not union:
            return 0.0
        return round(len(intersection) / len(union), 6)

    @staticmethod
    def compute_combined_score(dense_sim: float, statutory_match: float) -> float:
        """
        Combined Sim(Q, Cj) × StatutoryMatch(Q, Cj) — VADP Field 4.

        This is the primary ranking signal of the Semantic Precedent Relator.
        The multiplication gates high-similarity results that have no statutory
        intersection, penalising lexically similar but legally irrelevant matches.
        """
        return round(float(dense_sim) * float(statutory_match), 6)

    @classmethod
    def score(
        cls,
        dense_sim: float,
        query_sections: list[str],
        candidate_sections: list[str],
    ) -> dict[str, float]:
        """
        Compute all three Semantic Precedent Relator scores in one call.

        Returns:
            {
              "dense_sim":       Sim(Q, Cj)               [Field 3],
              "statutory_match": StatutoryMatch(Q, Cj),
              "combined_score":  Sim × StatutoryMatch      [Field 4],
            }
        """
        statutory_match = cls.compute_statutory_match(
            query_sections, candidate_sections
        )
        combined = cls.compute_combined_score(dense_sim, statutory_match)
        return {
            "dense_sim": round(float(dense_sim), 6),
            "statutory_match": statutory_match,
            "combined_score": combined,
        }


# ── LTR Feature Schema ───────────────────────────────────────────────────────


class LTRCandidateFeatures(BaseModel):
    chunk_id: str
    query_id: str
    relevance_label: int  # 0 (irrelevant) to 3 (perfect match)

    # Field 3 — Dense cosine similarity Sim(Q, Cj)
    dense_similarity: float
    # Field 4 — Combined Sim × StatutoryMatch (Semantic Precedent Relator)
    statutory_match_score: float = 0.0
    combined_relator_score: float = 0.0  # = dense_similarity × statutory_match_score

    # Remaining IR features
    bm25_score: float
    temporal_recency: float
    bench_relevance: float
    bsa_evidence_alignment: float
    citation_centrality: float

    def to_feature_vector(self) -> list[float]:
        """8-dimensional feature vector for LambdaMART training."""
        return [
            self.dense_similarity,  # Feature 1: Sim(Q, Cj)
            self.bm25_score,  # Feature 2: BM25 lexical
            self.statutory_match_score,  # Feature 3: StatutoryMatch(Q, Cj)
            self.combined_relator_score,  # Feature 4: Sim × StatutoryMatch [KEY SIGNAL]
            self.temporal_recency,  # Feature 5: Recency decay
            self.bench_relevance,  # Feature 6: Bench/coram relevance
            self.bsa_evidence_alignment,  # Feature 7: BSA §63(4) alignment
            self.citation_centrality,  # Feature 8: Citation graph PageRank
        ]


# ── LambdaMART Learning-to-Rank Engine ──────────────────────────────────────


class LambdaMARTLearningToRank:
    """
    Formal LambdaMART Pairwise Learning-to-Rank (LTR) engine.

    Uses XGBoost rank:pairwise objective over 8 IR features including
    the dynamic Sim(Q,Cj) × StatutoryMatch(Q,Cj) combined score as the
    primary Semantic Precedent Relator signal (replaces static weights).

    Fallback (untrained model): ranks by combined_relator_score directly.
    """

    FEATURE_NAMES = [
        "dense_similarity",
        "bm25_score",
        "statutory_match_score",
        "combined_relator_score",  # Semantic Precedent Relator — VADP Field 3×4
        "temporal_recency",
        "bench_relevance",
        "bsa_evidence_alignment",
        "citation_centrality",
    ]

    def __init__(
        self,
        n_estimators: int = 30,
        learning_rate: float = 0.08,
        max_depth: int = 3,
    ) -> None:
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.model = None
        self._init_ranker()

    def _init_ranker(self) -> None:
        """Initialise XGBoost LambdaMART ranker (rank:pairwise objective)."""
        try:
            import xgboost as xgb

            self.model = xgb.XGBRanker(
                objective="rank:pairwise",
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                random_state=42,
            )
        except Exception:
            self.model = None

    def fit(self, X: np.ndarray, y: np.ndarray, group: list[int]) -> None:
        """
        Train XGBoost LambdaMART pairwise ranker on candidate query groups.

        X: (N, 8) feature matrix
        y: (N,) relevance grades (0..3)
        group: list of group sizes per query
        """
        if self.model is not None:
            self.model.fit(X, y, group=group)

    def compute_ranking_score(self, candidate: LTRCandidateFeatures) -> float:
        """
        Compute pairwise ranking score.

        If LambdaMART model is trained: uses XGBoost prediction.
        If untrained: falls back to combined_relator_score (Sim × StatutoryMatch).
        """
        vec = np.array([candidate.to_feature_vector()])

        if self.model is not None and getattr(self.model, "_Booster", None) is not None:
            return float(round(float(self.model.predict(vec)[0]), 6))

        # Fallback: use the Semantic Precedent Relator combined score directly
        return float(round(candidate.combined_relator_score, 6))

    def rank_candidates(
        self,
        candidates: list[LTRCandidateFeatures],
    ) -> list[tuple[LTRCandidateFeatures, float]]:
        """Rank candidate list by LambdaMART or Semantic Precedent Relator score (descending)."""
        if not candidates:
            return []

        if self.model is not None and getattr(self.model, "_Booster", None) is not None:
            X = np.array([c.to_feature_vector() for c in candidates])
            scores = self.model.predict(X)
            scored = [(cand, float(round(s, 6))) for cand, s in zip(candidates, scores)]
        else:
            # Fallback: sort by combined Semantic Precedent Relator score
            scored = [(cand, self.compute_ranking_score(cand)) for cand in candidates]

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    @staticmethod
    def build_candidate(
        chunk_id: str,
        query_id: str,
        dense_similarity: float,
        query_sections: list[str],
        candidate_sections: list[str],
        bm25_score: float = 0.0,
        temporal_recency: float = 0.5,
        bench_relevance: float = 0.5,
        bsa_evidence_alignment: float = 0.5,
        citation_centrality: float = 0.5,
        relevance_label: int = 0,
    ) -> LTRCandidateFeatures:
        """
        Convenience factory that auto-computes the Semantic Precedent Relator scores.

        Call this instead of constructing LTRCandidateFeatures manually — it
        ensures Field 3 (statutory_match_score) and Field 4 (combined_relator_score)
        are always dynamically computed.
        """
        relator_scores = SemanticPrecedentRelator.score(
            dense_sim=dense_similarity,
            query_sections=query_sections,
            candidate_sections=candidate_sections,
        )
        return LTRCandidateFeatures(
            chunk_id=chunk_id,
            query_id=query_id,
            relevance_label=relevance_label,
            dense_similarity=dense_similarity,
            statutory_match_score=relator_scores["statutory_match"],
            combined_relator_score=relator_scores["combined_score"],
            bm25_score=bm25_score,
            temporal_recency=temporal_recency,
            bench_relevance=bench_relevance,
            bsa_evidence_alignment=bsa_evidence_alignment,
            citation_centrality=citation_centrality,
        )
