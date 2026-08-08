"""
Normalized Semantic Self-Consistency (NSSC) Score — VADP Field 7
================================================================

Computes Normalized Semantic Self-Consistency (NSSC) for generative
LLM completions to measure text reliability.

Algorithm:
  1. Generate 3 completions at temperature T=0.7 via Groq API (LLM_MODEL)
  2. Encode all 3 using all-MiniLM-L6-v2 (same model as RAG embeddings)
  3. Compute pairwise cosine similarity across C(3,2)=3 pairs
  4. NSSC = mean of 3 pairwise similarities ∈ [0, 1]
  5. If NSSC < NSSC_THRESHOLD (0.82) → set escalation_required = True

VADP Contract Binding:
  Field 7: generative_reliability_score = NSSC ∈ [0, 1]
           escalation_required: bool — mandatory human escalation flag

References:
  Wang et al. (2023) "Self-Consistency Improves Chain of Thought Reasoning"
  All-MiniLM-L6-v2: sentence-transformers/all-MiniLM-L6-v2
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logger = logging.getLogger(__name__)

# ── NSSC Configuration ───────────────────────────────────────────────────────

NSSC_THRESHOLD: float = 0.82  # Escalation mandatory if NSSC < this value
NSSC_TEMPERATURE: float = 0.7  # Sampling temperature for diversity
NSSC_N_COMPLETIONS: int = 3  # Number of independent completions
NSSC_MAX_TOKENS: int = 512  # Max tokens per completion

_encoder_instance = None  # Lazy-loaded sentence-transformer


# ── Encoder ─────────────────────────────────────────────────────────────────


def _get_encoder():
    """Lazy-load the all-MiniLM-L6-v2 sentence-transformer encoder."""
    global _encoder_instance
    if _encoder_instance is None:
        try:
            from sentence_transformers import SentenceTransformer

            _encoder_instance = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded all-MiniLM-L6-v2 for NSSC computation.")
        except ImportError:
            logger.warning("sentence-transformers not available — using fallback encoder.")
            _encoder_instance = None
    return _encoder_instance


def _fallback_encode(texts: list[str]) -> np.ndarray:
    """Deterministic 384-dim encoding fallback (mirrors EmbeddingGenerator)."""
    import hashlib

    vectors = []
    for text in texts:
        key_bytes = hashlib.pbkdf2_hmac("sha256", text.encode(), b"nssc_salt", 1, dklen=1536)
        raw = np.frombuffer(key_bytes, dtype=np.float32)
        norm = np.linalg.norm(raw)
        vectors.append(raw / norm if norm > 0 else raw)
    return np.array(vectors, dtype=np.float32)


def encode_texts(texts: list[str]) -> np.ndarray:
    """Encode texts to normalized embeddings using all-MiniLM-L6-v2."""
    encoder = _get_encoder()
    if encoder is not None:
        embeddings = encoder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype(np.float32)
    return _fallback_encode(texts)


# ── NSSC Computation ─────────────────────────────────────────────────────────


def compute_pairwise_cosine_mean(embeddings: np.ndarray) -> float:
    """
    Compute mean pairwise cosine similarity across all C(N,2) pairs.

    For N=3: computes [(0,1), (0,2), (1,2)] = 3 pairs.
    Embeddings should be L2-normalized (cosine = dot product).
    """
    n = embeddings.shape[0]
    scores: list[float] = []

    for i in range(n):
        for j in range(i + 1, n):
            # Cosine similarity for normalized vectors = dot product
            score = float(np.dot(embeddings[i], embeddings[j]))
            scores.append(max(0.0, min(1.0, score)))  # clip to [0, 1]

    return float(np.mean(scores)) if scores else 0.0


def compute_nssc(completions: list[str]) -> float:
    """
    Compute NSSC from a list of text completions.

    Args:
        completions: List of text completions (at least 2 required)

    Returns:
        NSSC score ∈ [0, 1]
    """
    if len(completions) < 2:
        return 1.0  # Cannot compute with < 2 samples — assume perfect consistency

    embeddings = encode_texts(completions)
    return round(compute_pairwise_cosine_mean(embeddings), 6)


def evaluate_nssc(nssc_score: float) -> dict[str, Any]:
    """
    Evaluate NSSC score and determine escalation requirement.

    Returns:
        {
          "nssc_score": float,
          "escalation_required": bool,
          "reliability_label": str,  # "HIGH" | "MEDIUM" | "LOW"
          "threshold": float,
        }
    """
    escalation_required = nssc_score < NSSC_THRESHOLD
    if nssc_score >= 0.90:
        reliability_label = "HIGH"
    elif nssc_score >= NSSC_THRESHOLD:
        reliability_label = "MEDIUM"
    else:
        reliability_label = "LOW"

    return {
        "nssc_score": nssc_score,
        "escalation_required": escalation_required,
        "reliability_label": reliability_label,
        "threshold": NSSC_THRESHOLD,
        "explanation": (
            f"NSSC={nssc_score:.4f} — {reliability_label} generative reliability. "
            + (
                f"⚠️ MANDATORY ESCALATION: NSSC below threshold ({NSSC_THRESHOLD}). "
                "Human review required before judicial use."
                if escalation_required
                else "Generative output is sufficiently consistent for judicial advisory use."
            )
        ),
    }


# ── LLM Completion Generator ─────────────────────────────────────────────────


class NSScorer:
    """
    NSSC scorer with live Groq API integration.

    Generates NSSC_N_COMPLETIONS independent completions at T=0.7,
    encodes with all-MiniLM-L6-v2, and computes pairwise cosine mean.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.groq.com/openai/v1",
        model: str = "llama-3.3-70b-versatile",
    ) -> None:
        # Load from env if not provided
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.base_url = base_url
        self.model = model

        if not self.api_key:
            try:
                from app.config import get_settings

                s = get_settings()
                self.api_key = s.LLM_API_KEY
                self.base_url = s.LLM_BASE_URL
                self.model = s.LLM_MODEL
            except Exception:
                pass

    def _generate_completion(self, prompt: str, timeout: int = 60) -> str:
        """Generate a single LLM completion via Groq API."""
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY not configured for NSSC live API.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": NSSC_MAX_TOKENS,
            "temperature": NSSC_TEMPERATURE,
            "stream": False,
        }

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    def score_prompt(
        self,
        prompt: str,
        n_completions: int = NSSC_N_COMPLETIONS,
    ) -> dict[str, Any]:
        """
        Generate n_completions at T=0.7, compute NSSC, return full result dict.

        Returns:
            {
              "completions": list[str],
              "nssc_score": float,           ← Field 7
              "escalation_required": bool,   ← Field 7
              "reliability_label": str,
              "threshold": float,
              "explanation": str,
            }
        """
        completions: list[str] = []
        errors: list[str] = []

        for i in range(n_completions):
            try:
                completion = self._generate_completion(prompt)
                completions.append(completion)
                logger.info(
                    "Generated completion %d/%d (len=%d)", i + 1, n_completions, len(completion)
                )
            except Exception as e:
                logger.warning("Completion %d failed: %s", i + 1, str(e))
                errors.append(str(e))

        if len(completions) < 2:
            # Cannot compute NSSC with < 2 completions
            logger.error(
                "NSSC: insufficient completions (%d). Errors: %s", len(completions), errors
            )
            return {
                "completions": completions,
                "nssc_score": 0.0,
                "escalation_required": True,
                "reliability_label": "LOW",
                "threshold": NSSC_THRESHOLD,
                "explanation": f"NSSC computation failed: insufficient completions ({len(completions)}/{n_completions}). Mandatory escalation.",
                "errors": errors,
            }

        nssc_score = compute_nssc(completions)
        evaluation = evaluate_nssc(nssc_score)

        return {
            "completions": completions,
            "n_completions_generated": len(completions),
            **evaluation,
            "errors": errors if errors else [],
        }
