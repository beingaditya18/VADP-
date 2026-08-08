"""
Explanation-Aware Re-ranker for VADP RAG Engine.

Jointly optimizes for retrieval precision AND SHAP explainability stability (sigma_SHAP):
Score(c_i) = alpha * Similarity(q, c_i) - beta * AttributionVariance(c_i)

This ensures retrieved context produces stable, non-volatile SHAP attributions,
improving overall explainability fidelity in Field 4 of the Verification Contract.
"""

from typing import List, Dict, Any
import numpy as np
from pydantic import BaseModel


class RerankedChunk(BaseModel):
    chunk_id: str
    original_rank: int
    new_rank: int
    similarity_score: float
    attribution_variance: float
    explanation_aware_score: float
    snippet: str


class ExplanationAwareReranker:
    """
    Re-ranks retrieved candidates by joint optimization of relevance and attribution stability.
    """

    def __init__(self, alpha: float = 0.70, beta: float = 0.30):
        """
        :param alpha: Weight for semantic relevance similarity S_rel
        :param beta: Penalty weight for SHAP attribution variance sigma_SHAP
        """
        self.alpha = alpha
        self.beta = beta

    def estimate_attribution_variance(self, chunk_text: str, query_text: str) -> float:
        """
        Estimates SHAP feature attribution variance (instability under perturbation)
        for a candidate chunk given a query.
        """
        # Heuristic: shorter, noise-heavy or keyword-dense text has higher variance under perturbation
        words = chunk_text.split()
        if not words:
            return 1.0

        length_factor = min(1.0, len(words) / 100.0)  # Optimal chunk length ~100 words
        unique_factor = len(set(words)) / len(words)  # Lexical diversity

        # Variance is higher for low diversity or extreme lengths
        stability = 0.6 * length_factor + 0.4 * unique_factor
        instability_variance = float(round(1.0 - max(0.0, min(1.0, stability)), 4))

        return instability_variance

    def rerank(
        self, candidates: List[Dict[str, Any]], query_text: str, top_k: int = 5
    ) -> List[RerankedChunk]:
        """
        Re-ranks candidates according to joint score:
        Score = alpha * Sim - beta * Variance
        """
        scored_chunks: List[RerankedChunk] = []

        for orig_idx, cand in enumerate(candidates):
            chunk_id = str(cand.get("id", cand.get("chunk_id", f"chunk_{orig_idx}")))
            sim_score = float(cand.get("score", cand.get("similarity", 0.5)))
            snippet = str(cand.get("content", cand.get("snippet", "")))

            attr_var = self.estimate_attribution_variance(snippet, query_text)
            
            # Joint score computation
            joint_score = float(round(self.alpha * sim_score - self.beta * attr_var, 4))

            scored_chunks.append(
                RerankedChunk(
                    chunk_id=chunk_id,
                    original_rank=orig_idx + 1,
                    new_rank=0,  # Will be populated after sorting
                    similarity_score=sim_score,
                    attribution_variance=attr_var,
                    explanation_aware_score=joint_score,
                    snippet=snippet,
                )
            )

        # Sort by explanation-aware score descending
        scored_chunks.sort(key=lambda x: x.explanation_aware_score, reverse=True)

        # Assign new ranks
        for new_idx, item in enumerate(scored_chunks):
            item.new_rank = new_idx + 1

        return scored_chunks[:top_k]
