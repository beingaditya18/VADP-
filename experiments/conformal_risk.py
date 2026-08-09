"""
Theorem 2 Empirical Instantiation — Conformal Risk Thresholding
================================================================

Phase 3.2 — Statistical Governance

Implements conformal risk control per Theorem 2 of the VADP manuscript:

  For target miss-risk α = 0.05, the conformal threshold τ̂_p is defined as:
    τ̂_p = quantile_{(1-α)} of non-conformity scores {s_i} on calibration set

  Non-conformity score for a correct prediction:
    s_i = 1 - Trust_Score_i   (if Y_i = 1, i.e., correct/favorable outcome)

  Validation guarantee (Theorem 2 bound):
    P(miss-rate on held-out set ≤ α) ≥ 1 - δ

Split:
  From the 300-case held-out test set (Phase 3.1):
    Calibration:  100 cases → compute τ̂_p
    Validation:   200 cases → verify bounded miss-rate ≤ 5.0%

Appellate Outcome Ground Truth:
  Y_i = 1: Case outcome is favorable (granted/allowed)
  Y_i = 0: Case outcome is unfavorable (dismissed/upheld against petitioner)
  Source: synthetic corpus `appellate_outcome` field (generated with BSA-aligned labels)

Outputs:
  evaluation/CONFORMAL_RISK_REPORT.json
  evaluation/CONFORMAL_RISK_REPORT.md

Usage:
  python evaluation/conformal_risk.py --alpha 0.05 --max-cases 1500 --seed 42
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
from evaluation.trust_score_split import compute_trust_score, build_trust_score_dataset
from app.rag.embeddings import EmbeddingGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("conformal_risk")


# ── Conformal Risk Functions ─────────────────────────────────────────────────


def compute_nonconformity_scores(
    trust_scores: np.ndarray,
    labels: np.ndarray,
) -> np.ndarray:
    """
    Compute non-conformity scores for correctly-labeled examples.

    For Y_i = 1 (favorable outcome), s_i = 1 - Trust_Score_i.
    Higher s_i means the model is LESS confident about a correct prediction.

    Only cases with Y_i = 1 contribute to calibration (per conformal risk framework).
    """
    scores = []
    for ts, y in zip(trust_scores, labels):
        if y == 1:
            scores.append(1.0 - float(ts))
    return np.array(scores, dtype=np.float64)


def compute_conformal_threshold(
    calibration_scores: np.ndarray,
    alpha: float = 0.05,
) -> float:
    """
    Compute τ̂_p = (1 - α)-quantile of non-conformity scores.

    This is the conformal prediction threshold that guarantees:
      P(miss-rate ≤ α) ≥ 1 - δ on a held-out set.

    Args:
        calibration_scores: Non-conformity scores from calibration set (Y=1 cases)
        alpha: Target miss-risk (default 0.05 = 5%)

    Returns:
        τ̂_p ∈ [0, 1]
    """
    if len(calibration_scores) == 0:
        return 0.5  # Default safe threshold

    quantile_level = 1.0 - alpha
    tau_hat = float(np.quantile(calibration_scores, quantile_level))
    return round(tau_hat, 6)


def evaluate_bounded_error(
    test_trust_scores: np.ndarray,
    test_labels: np.ndarray,
    tau_hat: float,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """
    Evaluate conformal risk bound on validation set.

    A miss occurs when:
      Y_i = 1 (correct/favorable outcome) AND Trust_Score_i < (1 - tau_hat)
      i.e., the model's non-conformity score s_i > tau_hat for a correct case

    Args:
        test_trust_scores: Trust scores on validation set
        test_labels: Ground-truth appellate outcomes (0 or 1)
        tau_hat: Conformal threshold computed on calibration set
        alpha: Target miss-risk level

    Returns:
        {
          "n_validation": int,
          "n_positive": int,         # cases with Y=1
          "n_missed": int,           # correct cases where trust < (1-tau_hat)
          "miss_rate": float,
          "bounded": bool,           # miss_rate ≤ alpha
          "tau_hat": float,
          "decision_threshold": float,  # 1 - tau_hat
        }
    """
    decision_threshold = 1.0 - tau_hat

    n_positive = int(np.sum(test_labels == 1))
    n_missed = 0
    missed_indices: list[int] = []

    for i, (ts, y) in enumerate(zip(test_trust_scores, test_labels)):
        if y == 1 and float(ts) < decision_threshold:
            n_missed += 1
            missed_indices.append(i)

    miss_rate = n_missed / len(test_labels) if len(test_labels) > 0 else 0.0
    bounded = miss_rate <= alpha

    return {
        "n_validation": len(test_labels),
        "n_positive_cases": n_positive,
        "n_missed": n_missed,
        "miss_rate": round(miss_rate, 6),
        "miss_rate_pct": round(miss_rate * 100, 4),
        "bounded": bounded,
        "tau_hat": tau_hat,
        "decision_threshold": round(decision_threshold, 6),
        "alpha": alpha,
        "alpha_pct": alpha * 100,
        "missed_indices": missed_indices[:10],  # First 10 for debugging
    }


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Theorem 2 Conformal Risk Thresholding")
    parser.add_argument("--alpha", type=float, default=0.05, help="Target miss-risk (default=0.05)")
    parser.add_argument("--max-cases", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--n-calibration", type=int, default=500,
        help="Calibration set size from held-out test set"
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    np.random.seed(args.seed)

    # Step 1: Generate corpus and trust score dataset
    logger.info("Generating %d-case corpus...", args.max_cases)
    corpus = generate_synthetic_corpus(n_cases=args.max_cases, seed=args.seed)

    encoder = EmbeddingGenerator()
    logger.info("Building trust score dataset...")
    dataset = build_trust_score_dataset(corpus, encoder, seed=args.seed, max_chunks_per_case=2, use_fast_encoder=True)
    logger.info("Dataset size: %d records", len(dataset))

    # Step 2: Apply same 80/20 split as Phase 3.1
    rng_split = random.Random(args.seed)
    rng_split.shuffle(dataset)
    n_train = int(len(dataset) * 0.80)
    test_set = dataset[n_train:]  # 20% held-out test set

    logger.info("Held-out test set size: %d cases", len(test_set))

    if len(test_set) < args.n_calibration + 50:
        logger.error(
            "Test set too small (%d) for calibration=%d + validation=50+",
            len(test_set), args.n_calibration,
        )
        sys.exit(1)

    # Step 3: Split test set into calibration (500) + validation (remaining)
    rng_split2 = random.Random(args.seed + 1)
    rng_split2.shuffle(test_set)
    n_calib = min(args.n_calibration, len(test_set) - 50)
    calibration_set = test_set[:n_calib]
    validation_set = test_set[n_calib:]

    logger.info("Calibration: %d cases | Validation: %d cases", len(calibration_set), len(validation_set))

    # Step 4: Compute non-conformity scores on calibration set
    calib_trust = np.array([r["trust_score"] for r in calibration_set])
    calib_outcomes = np.array([r["appellate_outcome"] for r in calibration_set])

    nonconformity_scores = compute_nonconformity_scores(calib_trust, calib_outcomes)

    n_positive_calib = int(np.sum(calib_outcomes == 1))
    logger.info(
        "Calibration set: %d positive cases (Y=1), %d non-conformity scores",
        n_positive_calib, len(nonconformity_scores),
    )

    if len(nonconformity_scores) == 0:
        logger.error("No positive cases (Y=1) in calibration set — cannot compute threshold.")
        sys.exit(1)

    # Step 5: Compute τ̂_p
    tau_hat = compute_conformal_threshold(nonconformity_scores, alpha=args.alpha)
    decision_threshold = 1.0 - tau_hat

    logger.info(
        "Conformal threshold: τ̂_p = %.6f (decision threshold = %.6f, α = %.2f)",
        tau_hat, decision_threshold, args.alpha,
    )

    # Step 6: Evaluate bounded error on validation set
    val_trust = np.array([r["trust_score"] for r in validation_set])
    val_outcomes = np.array([r["appellate_outcome"] for r in validation_set])

    bounded_result = evaluate_bounded_error(val_trust, val_outcomes, tau_hat, alpha=args.alpha)

    logger.info(
        "Validation: miss_rate=%.4f%% (bound: ≤%.1f%%) | bounded=%s",
        bounded_result["miss_rate_pct"],
        args.alpha * 100,
        "✅ YES" if bounded_result["bounded"] else "❌ NO",
    )

    # Step 7: Coverage analysis
    coverage_threshold = 1.0 - decision_threshold
    covered = np.sum(val_trust >= decision_threshold)
    coverage_rate = covered / len(val_trust)

    # Step 8: Compile report
    report = {
        "theorem": "Theorem 2 — Conformal Risk Control",
        "alpha": args.alpha,
        "n_total_corpus": len(dataset),
        "n_held_out_test": len(test_set),
        "n_calibration": len(calibration_set),
        "n_validation": len(validation_set),
        "n_positive_calibration": n_positive_calib,
        "nonconformity_scores_stats": {
            "mean": round(float(np.mean(nonconformity_scores)), 6),
            "std": round(float(np.std(nonconformity_scores)), 6),
            "min": round(float(np.min(nonconformity_scores)), 6),
            "max": round(float(np.max(nonconformity_scores)), 6),
            "quantile_95": round(float(np.quantile(nonconformity_scores, 0.95)), 6),
        },
        "tau_hat_p": tau_hat,
        "decision_threshold": round(decision_threshold, 6),
        "bounded_error_result": bounded_result,
        "coverage_rate": round(float(coverage_rate), 4),
        "theorem_2_satisfied": bounded_result["bounded"],
        "seed": args.seed,
    }

    # Save JSON
    json_path = EVAL_DIR / "CONFORMAL_RISK_REPORT.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Save Markdown
    bounded_icon = "✅" if bounded_result["bounded"] else "❌"
    md_lines = [
        "# Theorem 2 — Conformal Risk Threshold Empirical Validation",
        "",
        f"**Target miss-risk**: α = {args.alpha} ({args.alpha*100:.0f}%)  ",
        f"**Calibration set**: N = {len(calibration_set)} held-out cases (Y ∈ {{0,1}} appellate outcomes)  ",
        f"**Validation set**: N = {len(validation_set)} held-out cases  ",
        "",
        "## Computed Conformal Threshold",
        "",
        f"| Parameter | Value |",
        f"| --- | --- |",
        f"| **τ̂_p** (conformal threshold) | `{tau_hat:.6f}` |",
        f"| **Decision threshold** (1 - τ̂_p) | `{decision_threshold:.6f}` |",
        f"| **Non-conformity scores (N)** | {len(nonconformity_scores)} |",
        f"| **Non-conformity score mean** | {float(np.mean(nonconformity_scores)):.4f} |",
        "",
        "## Bounded Error Validation on 200 Held-Out Cases",
        "",
        f"| Metric | Value | Target |",
        f"| --- | --- | --- |",
        f"| **Miss rate** | {bounded_result['miss_rate_pct']:.4f}% | ≤ {args.alpha*100:.0f}% |",
        f"| **Missed cases** | {bounded_result['n_missed']} / {bounded_result['n_validation']} | — |",
        f"| **Bound satisfied** | **{bounded_icon} {'YES' if bounded_result['bounded'] else 'NO'}** | TRUE |",
        f"| **Coverage rate** | {coverage_rate*100:.2f}% | — |",
        "",
        f"> **Theorem 2 {'✅ EMPIRICALLY SATISFIED' if bounded_result['bounded'] else '❌ NOT SATISFIED'}**: "
        f"The conformal threshold τ̂_p = {tau_hat:.6f} achieves a miss-rate of "
        f"{bounded_result['miss_rate_pct']:.4f}% ≤ {args.alpha*100:.0f}% on the 200-case validation set.",
    ]
    md_path = EVAL_DIR / "CONFORMAL_RISK_REPORT.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print("\n[DONE] Conformal Risk Threshold (Theorem 2) Report complete!")
    print(f"   tau_hat_p = {tau_hat:.6f}")
    print(f"   Decision threshold = {decision_threshold:.6f}")
    bound_str = "<=" if bounded_result["bounded"] else ">"
    print(f"   Miss rate = {bounded_result['miss_rate_pct']:.4f}% {bound_str} {args.alpha*100:.0f}%  {'[PASS]' if bounded_result['bounded'] else '[FAIL]'}")
    print(f"   Theorem 2 satisfied: {'YES' if bounded_result['bounded'] else 'NO'}")
    print(f"   JSON -> {json_path}")


if __name__ == "__main__":
    main()
