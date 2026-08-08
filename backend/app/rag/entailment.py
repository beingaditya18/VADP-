"""
Citation Entailment Verification Module for VADP RAG Engine.

Directly addresses legal AI hallucination risks (Dahl et al. / RegLab) by checking
whether retrieved legal chunks actually entail/support the LLM's generated claims
before populating Field 3 (Citation Provenance) of the Verification Contract.
"""

from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class EntailmentResult(BaseModel):
    chunk_id: str
    premise_snippet: str
    claim_hypothesis: str
    entailment_score: float = Field(ge=0.0, le=1.0)
    entailment_status: str = Field(description="'entailed' | 'neutral' | 'contradiction'")
    is_supported: bool


class CitationEntailmentVerifier:
    """
    Evaluates semantic and NLI entailment between retrieved chunk premises
    and generated claim hypotheses.
    Supports real DeBERTa-v3 NLI CrossEncoder inference with lazy loading
    and fast heuristic fallback.
    """

    _model: Any = None
    _model_name: str = "cross-encoder/nli-deberta-v3-large"

    def __init__(self, entailment_threshold: float = 0.50, use_nli_model: bool = True):
        self.threshold = entailment_threshold
        self.use_nli_model = use_nli_model

    @classmethod
    def _get_nli_model(cls) -> Any:
        """Lazy loader for DeBERTa-v3 CrossEncoder model."""
        if cls._model is None:
            try:
                import logging

                from sentence_transformers import CrossEncoder

                logging.getLogger(__name__).info(
                    "Loading DeBERTa NLI CrossEncoder model: %s", cls._model_name
                )
                cls._model = CrossEncoder(cls._model_name)
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(
                    "Failed to load DeBERTa CrossEncoder (%s); using fallback heuristic.", e
                )
                cls._model = False
        return cls._model if cls._model is not False else None

    def verify_chunk_entailment(
        self, chunk_id: str, premise_text: str, claim_text: str
    ) -> EntailmentResult:
        """
        Computes entailment score between premise and claim.
        Uses real DeBERTa-v3 NLI CrossEncoder if available, otherwise falls back to token overlap heuristic.
        """
        if not claim_text.strip():
            return EntailmentResult(
                chunk_id=chunk_id,
                premise_snippet=premise_text[:200],
                claim_hypothesis=claim_text,
                entailment_score=0.0,
                entailment_status="neutral",
                is_supported=False,
            )

        model = self._get_nli_model() if self.use_nli_model else None

        if model is not None:
            try:
                # DeBERTa-v3 NLI predicts logits over [contradiction, entailment, neutral]
                scores = model.predict([(premise_text, claim_text)])
                if len(scores.shape) == 2:
                    probs = np.exp(scores[0]) / np.sum(np.exp(scores[0]))
                    # Index mapping: 0=contradiction, 1=entailment, 2=neutral (standard MNLI mapping)
                    p_contra, p_entail, p_neutral = (
                        float(probs[0]),
                        float(probs[1]),
                        float(probs[2]),
                    )
                else:
                    p_entail = float(scores[0])
                    p_contra = 1.0 - p_entail

                if p_entail >= 0.60:
                    status = "entailed"
                    is_supported = True
                elif p_contra >= 0.60:
                    status = "contradiction"
                    is_supported = False
                else:
                    status = "neutral"
                    is_supported = p_entail >= self.threshold

                return EntailmentResult(
                    chunk_id=chunk_id,
                    premise_snippet=premise_text[:200],
                    claim_hypothesis=claim_text[:200],
                    entailment_score=float(round(p_entail, 4)),
                    entailment_status=status,
                    is_supported=is_supported,
                )
            except Exception:
                pass  # Fallback to heuristic

        # Fallback Lexical Jaccard & Term Coverage Heuristic
        premise_words = set(premise_text.lower().split())
        claim_words = set(claim_text.lower().split())

        intersection = premise_words.intersection(claim_words)
        union = premise_words.union(claim_words)
        jaccard_score = len(intersection) / len(union) if union else 0.0
        coverage_score = len(intersection) / len(claim_words) if claim_words else 0.0

        score = float(round(0.4 * jaccard_score + 0.6 * coverage_score, 4))
        rescaled_score = float(round(min(1.0, max(0.0, 0.3 + 0.7 * score)), 4))

        if rescaled_score >= 0.70:
            status = "entailed"
            is_supported = True
        elif rescaled_score >= self.threshold:
            status = "neutral"
            is_supported = True
        else:
            status = "contradiction"
            is_supported = False

        return EntailmentResult(
            chunk_id=chunk_id,
            premise_snippet=premise_text[:200],
            claim_hypothesis=claim_text[:200],
            entailment_score=rescaled_score,
            entailment_status=status,
            is_supported=is_supported,
        )

    def filter_citations(
        self, citations: list[dict[str, Any]], generated_claim: str
    ) -> tuple[list[dict[str, Any]], list[EntailmentResult]]:
        """
        Filters citation list, annotating each citation with its entailment verification result.
        """
        verified_citations = []
        entailment_results = []

        for cit in citations:
            chunk_id = str(cit.get("chunk_id", cit.get("id", "unknown")))
            snippet = str(cit.get("snippet", cit.get("content", "")))

            res = self.verify_chunk_entailment(chunk_id, snippet, generated_claim)
            entailment_results.append(res)

            # Annotate citation with entailment score
            cit_copy = dict(cit)
            cit_copy["entailment_score"] = res.entailment_score
            cit_copy["entailment_status"] = res.entailment_status
            cit_copy["is_supported"] = res.is_supported

            if res.is_supported:
                verified_citations.append(cit_copy)

        return verified_citations, entailment_results
