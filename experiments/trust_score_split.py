"""
Strict Out-of-Sample Trust Score Split with Platt Scaling
==========================================================

Phase 3.1 — Statistical Governance

Enforces STRICT disjoint 80/20 train/test split on 1,500 synthetic cases:
  Train set:  1,200 cases (80%) — Platt scaling logistic regression fitting ONLY
  Test set:     300 cases (20%) — held-out, NEVER touched during calibration

Reports ALL metrics exclusively on the held-out test set:
  - Pearson r      — linear correlation between Trust Score and ground-truth relevance
  - Spearman ρ     — monotonic rank-order preservation
  - ECE (before)   — Expected Calibration Error before Platt scaling
  - ECE (after)    — Expected Calibration Error after Platt scaling
  - Platt sigmoid  — a, b parameters of logistic calibration

Why this matters:
  The previous run_eval.py evaluated on the SAME data used for analysis
  (in-sample evaluation). This module fixes that critical statistical flaw.

Outputs:
  evaluation/TRUST_SCORE_SPLIT_REPORT.json
  evaluation/TRUST_SCORE_SPLIT_REPORT.md

Usage:
  python evaluation/trust_score_split.py --max-cases 1500 --seed 42
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from evaluation.corpus_generator import generate_synthetic_corpus
from app.rag.chunker import TextChunker
from app.rag.embeddings import EmbeddingGenerator

import faiss

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("trust_score_split")

N_BINS = 10       # Calibration bins for ECE


# ── Trust Score Formula ──────────────────────────────────────────────────────


def compute_trust_score(
    model_confidence: float,
    evidence_quality: float,
    source_reliability: float,
    semantic_consistency: float,
    alpha: float = 0.35,
    beta: float = 0.35,
    gamma: float = 0.15,
    delta: float = 0.15,
) -> float:
    """
    VADP Trust Score formula:
    TS = α·model_confidence + β·evidence_quality + γ·source_reliability + δ·semantic_consistency

    Weights (α=0.35, β=0.35, γ=0.15, δ=0.15) per VADP specification.
    """
    return (
        alpha * model_confidence
        + beta * evidence_quality
        + gamma * source_reliability
        + delta * semantic_consistency
    )


# ── Expected Calibration Error ────────────────────────────────────────────────


def compute_ece(
    trust_scores: np.ndarray,
    ground_truth_labels: np.ndarray,
    n_bins: int = N_BINS,
) -> tuple[float, list[dict[str, Any]]]:
    """
    Compute Expected Calibration Error (ECE).

    ECE = Σ_{b=1}^{B} (|B_b| / n) × |acc(B_b) - conf(B_b)|

    Where acc(B_b) = mean ground-truth in bin b, conf(B_b) = mean trust score in bin b.

    Returns:
        (ece_value: float, bin_details: list[dict])
    """
    bins = np.linspace(0, 1, n_bins + 1)
    bin_details = []
    n = len(trust_scores)
    ece = 0.0

    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        in_bin = np.where((trust_scores >= lo) & (trust_scores < hi))[0]

        if len(in_bin) == 0:
            continue

        avg_conf = float(np.mean(trust_scores[in_bin]))
        avg_acc = float(np.mean(ground_truth_labels[in_bin]))
        weight = len(in_bin) / n
        gap = abs(avg_conf - avg_acc)
        ece += weight * gap

        bin_details.append({
            "bin_range": f"[{lo:.2f}, {hi:.2f})",
            "sample_count": len(in_bin),
            "avg_trust_score": round(avg_conf, 4),
            "avg_gt_relevance": round(avg_acc, 4),
            "calibration_gap": round(gap, 4),
            "weight": round(weight, 4),
        })

    return round(ece, 6), bin_details


# ── Platt Scaling Calibration ────────────────────────────────────────────────


def platt_scaling(
    train_scores: np.ndarray,
    train_labels: np.ndarray,
    test_scores: np.ndarray,
) -> tuple[np.ndarray, float, float]:
    """
    Fit Platt scaling (logistic regression) on train set.
    Apply calibration to test scores.

    Returns:
        (calibrated_test_scores, platt_a, platt_b)
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    # Fit calibrator on training data only
    train_scores_2d = train_scores.reshape(-1, 1)
    calibrator = LogisticRegression(random_state=42, max_iter=1000)
    calibrator.fit(train_scores_2d, (train_labels > 0.5).astype(int))

    # Extract Platt sigmoid parameters
    platt_a = float(calibrator.coef_[0][0])
    platt_b = float(calibrator.intercept_[0])

    # Apply to test set
    test_scores_2d = test_scores.reshape(-1, 1)
    calibrated = calibrator.predict_proba(test_scores_2d)[:, 1]

    return calibrated.astype(np.float64), platt_a, platt_b


# ── Correlation Metrics ────────────────────────────────────────────────────


def pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation coefficient."""
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank-order correlation coefficient."""
    from scipy.stats import spearmanr
    result = spearmanr(x, y)
    return float(result.statistic)


# ── Dataset Builder ──────────────────────────────────────────────────────────


def build_trust_score_dataset(
    corpus: list[dict[str, Any]],
    encoder: EmbeddingGenerator,
    seed: int = 42,
    max_chunks_per_case: int = 2,
    use_fast_encoder: bool = False,
) -> list[dict[str, Any]]:
    """
    Build a dataset of (trust_score, ground_truth_relevance) pairs from corpus.

    Ground-truth relevance is proxied by:
      - Retrieval success (chunk recall@5 > 0) → relevance = 1.0
      - No retrieval hit                        → relevance = 0.0

    Trust score components are synthesized from embedding similarity + metadata.
    """
    rng = random.Random(seed)
    dataset: list[dict[str, Any]] = []

    import faiss

    logger.info("Building trust score dataset from %d cases...", len(corpus))

    # Build mini FAISS index for retrieval simulation
    all_chunks: list[str] = []
    all_chunk_ids: list[str] = []
    all_case_ids: list[str] = []
    sections_by_chunk: dict[str, list[str]] = {}

    for case_idx, case_data in enumerate(corpus):
        full_text = case_data.get("full_text", "")
        if not full_text or len(full_text.strip()) < 100:
            continue
        entities = case_data.get("entities", {})
        case_id = f"CASE_SPLIT_{case_idx:05d}"
        sections = [
            f"{s.get('section', '')} {s.get('act', '')}".strip()
            for s in entities.get("sections", [])
        ]
        chunks = TextChunker.chunk_text(full_text, chunk_size_chars=1500, overlap_chars=200)
        for c_idx, chunk in enumerate(chunks[:max_chunks_per_case]):
            cid = f"{case_id}_chk_{c_idx}"
            all_chunks.append(chunk)
            all_chunk_ids.append(cid)
            all_case_ids.append(case_id)
            sections_by_chunk[cid] = sections

    logger.info("Encoding %d chunks...", len(all_chunks))
    if use_fast_encoder:
        from sklearn.feature_extraction.text import HashingVectorizer
        vectorizer = HashingVectorizer(n_features=256, norm='l2')
        embeddings = vectorizer.transform(all_chunks).toarray().astype(np.float32)
    else:
        embeddings = encoder.encode(all_chunks)
        faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # For each case generate a query, retrieve, and compute trust score
    for case_idx, case_data in enumerate(corpus):
        full_text = case_data.get("full_text", "")
        if not full_text or len(full_text.strip()) < 100:
            continue
        entities = case_data.get("entities", {})
        case_id = f"CASE_SPLIT_{case_idx:05d}"
        topics = [t.get("text", "") for t in entities.get("topics", []) if t.get("text")]
        sections = [
            f"{s.get('section', '')} {s.get('act', '')}".strip()
            for s in entities.get("sections", [])
        ]
        summary = entities.get("summary", {}).get("summary", "")
        if not summary or not topics:
            continue

        # Synthesize abstractive query
        query_text = (
            f"In a matter concerning {topics[0]}, "
            f"what are the governing principles under {sections[0] if sections else 'Indian law'}?"
        )

        # Encode query and retrieve
        if use_fast_encoder:
            q_vec = vectorizer.transform([query_text]).toarray().astype(np.float32)
        else:
            q_vec = encoder.encode([query_text])
            faiss.normalize_L2(q_vec)
        k_retrieve = 5
        scores_ret, indices_ret = index.search(q_vec, k_retrieve)

        # Check if any result belongs to the correct case
        hit = any(
            all_case_ids[idx] == case_id
            for idx in indices_ret[0]
            if idx != -1 and idx < len(all_case_ids)
        )
        ground_truth_relevance = 1.0 if hit else 0.0

        # Compute trust score components
        top_score = float(scores_ret[0][0]) if len(scores_ret[0]) > 0 else 0.3
        model_confidence = max(0.0, min(1.0, top_score + rng.gauss(0, 0.05)))
        evidence_quality = max(0.0, min(1.0, rng.uniform(0.5, 0.9)))
        source_reliability = max(0.0, min(1.0, rng.uniform(0.6, 0.95)))
        semantic_consistency = max(0.0, min(1.0, top_score * 0.8 + rng.gauss(0, 0.03)))

        trust_score = compute_trust_score(
            model_confidence, evidence_quality, source_reliability, semantic_consistency
        )
        trust_score = max(0.0, min(1.0, trust_score))

        dataset.append({
            "case_id": case_id,
            "query_text": query_text,
            "trust_score": round(trust_score, 6),
            "ground_truth_relevance": ground_truth_relevance,
            "appellate_outcome": case_data.get("appellate_outcome", 0),
            "model_confidence": round(model_confidence, 4),
            "evidence_quality": round(evidence_quality, 4),
            "source_reliability": round(source_reliability, 4),
            "semantic_consistency": round(semantic_consistency, 4),
            "retrieval_hit": hit,
        })

        if (case_idx + 1) % 300 == 0:
            logger.info("  Built %d/%d records...", len(dataset), len(corpus))

    return dataset


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Strict 80/20 OOS Trust Score Split with Platt Scaling")
    parser.add_argument("--max-cases", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    from scipy.stats import pearsonr

    rng = random.Random(args.seed)
    np.random.seed(args.seed)

    # Step 1: Generate corpus
    logger.info("Generating %d-case synthetic corpus...", args.max_cases)
    corpus = generate_synthetic_corpus(n_cases=args.max_cases, seed=args.seed)

    # Step 2: Build trust score dataset
    encoder = EmbeddingGenerator()
    dataset = build_trust_score_dataset(corpus, encoder, seed=args.seed)
    logger.info("Dataset built: %d records", len(dataset))

    if len(dataset) < 50:
        logger.error("Insufficient dataset size for split analysis.")
        sys.exit(1)

    # Step 3: STRICT 80/20 split (shuffled, then split)
    random.Random(args.seed).shuffle(dataset)
    n_train = int(len(dataset) * 0.80)
    train_set = dataset[:n_train]
    test_set = dataset[n_train:]

    logger.info(
        "Split: Train=%d (%.0f%%), Test=%d (%.0f%%)",
        len(train_set), len(train_set)/len(dataset)*100,
        len(test_set), len(test_set)/len(dataset)*100,
    )

    train_scores = np.array([r["trust_score"] for r in train_set])
    train_gt = np.array([r["ground_truth_relevance"] for r in train_set])
    test_scores = np.array([r["trust_score"] for r in test_set])
    test_gt = np.array([r["ground_truth_relevance"] for r in test_set])

    # Step 4: Metrics on HELD-OUT TEST SET (raw, before Platt scaling)
    r_before = pearson_r(test_scores, test_gt)
    rho_before = spearman_rho(test_scores, test_gt)
    ece_before, bins_before = compute_ece(test_scores, test_gt)

    logger.info("Before Platt: Pearson r=%.4f, Spearman ρ=%.4f, ECE=%.4f", r_before, rho_before, ece_before)

    # Step 5: Platt scaling calibration (fit on TRAIN, apply to TEST)
    try:
        test_calibrated, platt_a, platt_b = platt_scaling(train_scores, train_gt, test_scores)

        r_after = pearson_r(test_calibrated, test_gt)
        rho_after = spearman_rho(test_calibrated, test_gt)
        ece_after, bins_after = compute_ece(test_calibrated, test_gt)

        logger.info("After Platt:  Pearson r=%.4f, Spearman ρ=%.4f, ECE=%.4f", r_after, rho_after, ece_after)
        platt_available = True

    except Exception as e:
        logger.warning("Platt scaling failed: %s", str(e))
        r_after, rho_after, ece_after, bins_after = r_before, rho_before, ece_before, bins_before
        platt_a, platt_b = 1.0, 0.0
        test_calibrated = test_scores
        platt_available = False

    # Step 6: Generate report
    report = {
        "n_total": len(dataset),
        "n_train": len(train_set),
        "n_test": len(test_set),
        "train_fraction": round(len(train_set) / len(dataset), 4),
        "test_fraction": round(len(test_set) / len(dataset), 4),
        "seed": args.seed,
        "split_method": "random_shuffle_80_20",
        "metrics_on_held_out_test_set": {
            "before_platt_scaling": {
                "pearson_r": round(r_before, 4),
                "spearman_rho": round(rho_before, 4),
                "ece": round(ece_before, 6),
                "mean_trust_score": round(float(np.mean(test_scores)), 4),
                "mean_ground_truth": round(float(np.mean(test_gt)), 4),
            },
            "after_platt_scaling": {
                "pearson_r": round(r_after, 4),
                "spearman_rho": round(rho_after, 4),
                "ece": round(ece_after, 6),
                "platt_a": round(platt_a, 4),
                "platt_b": round(platt_b, 4),
                "platt_available": platt_available,
                "ece_improvement": round(ece_before - ece_after, 6),
            },
        },
        "calibration_bins_before": bins_before[:5],   # First 5 bins for report
        "calibration_bins_after": bins_after[:5],
    }

    # Save JSON
    json_path = EVAL_DIR / "TRUST_SCORE_SPLIT_REPORT.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Save Markdown
    md_lines = [
        "# VADP Trust Score Out-of-Sample Validation Report",
        "",
        f"**Total cases**: {report['n_total']:,} | **Train**: {report['n_train']:,} (80%) | **Test**: {report['n_test']:,} (20%)",
        f"**Split seed**: `{report['seed']}` | **Method**: Strict disjoint random shuffle",
        "",
        "> [!WARNING]",
        "> All metrics below are computed **exclusively on the held-out test set (N={:,})**. The train set was used ONLY for Platt scaling calibration.".format(report["n_test"]),
        "",
        "## Metrics on Held-Out Test Set",
        "",
        "| Metric | Before Platt Scaling | After Platt Scaling | Improvement |",
        "| --- | --- | --- | --- |",
        f"| **Pearson r** | {r_before:.4f} | {r_after:.4f} | {r_after-r_before:+.4f} |",
        f"| **Spearman ρ** | {rho_before:.4f} | {rho_after:.4f} | {rho_after-rho_before:+.4f} |",
        f"| **ECE** | {ece_before:.6f} | {ece_after:.6f} | {ece_before-ece_after:+.6f} |",
        "",
        f"**Platt sigmoid**: a={platt_a:.4f}, b={platt_b:.4f}",
    ]
    md_path = EVAL_DIR / "TRUST_SCORE_SPLIT_REPORT.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"\n✅ Trust Score OOS Split Report complete!")
    print(f"   Pearson r (after):  {r_after:.4f}")
    print(f"   Spearman ρ (after): {rho_after:.4f}")
    print(f"   ECE (before):       {ece_before:.6f}")
    print(f"   ECE (after):        {ece_after:.6f}")
    print(f"   JSON → {json_path}")


if __name__ == "__main__":
    main()
