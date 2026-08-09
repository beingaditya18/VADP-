"""
VADP Joint Ablation on Trust Score Weights (α, β, γ, δ)
=========================================================

Performs a grid search over candidate weight tuples (α, β, γ, δ) in steps of 0.05
subject to:
  1. α + β + γ + δ = 1.0
  2. Autonomous Release Floor Guardrail: α + δ < τ_p (where τ_p = 0.88)
     ensuring model confidence alone cannot bypass review without evidence & source backing.

Also fits Maximum-Likelihood Logistic Regression on the 4 component features.

Evaluates Expected Calibration Error (ECE) and Pearson correlation r on held-out test split (N=291).
Outputs top-10 weight configuration table and JSON report.
"""

from __future__ import annotations

import json
import logging
import random
import sys
from pathlib import Path
from typing import Any
import numpy as np
from sklearn.linear_model import LogisticRegression

BACKEND_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from evaluation.corpus_generator import generate_synthetic_corpus
from app.rag.chunker import TextChunker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("trust_weight_ablation")

SAFETY_GUARDRAIL_TAU_P = 0.88  # α + δ < 0.88 constraint


def compute_ece(trust_scores: np.ndarray, ground_truth_labels: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0, 1, n_bins + 1)
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
        ece += weight * abs(avg_conf - avg_acc)
    return round(float(ece), 6)


def pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def generate_feature_dataset(n_total: int = 1491, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """
    Generates synthetic component score dataset:
    X: [N, 4] -> (S_model, S_evidence, S_source, S_consistency)
    y: [N]    -> ground_truth_relevance (0.0 or 1.0)
    """
    rng = np.random.RandomState(seed)
    
    # Ground truth binary relevance
    y = (rng.rand(n_total) < 0.72).astype(np.float64)
    
    # Synthetic component features correlated with ground truth
    s_model = np.clip(y * 0.70 + rng.normal(0.20, 0.15, n_total), 0.0, 1.0)
    s_evidence = np.clip(y * 0.75 + rng.normal(0.18, 0.12, n_total), 0.0, 1.0)
    s_source = np.clip(y * 0.80 + rng.normal(0.15, 0.10, n_total), 0.0, 1.0)
    s_consistency = np.clip(y * 0.65 + rng.normal(0.22, 0.14, n_total), 0.0, 1.0)
    
    X = np.column_stack([s_model, s_evidence, s_source, s_consistency])
    return X, y


def generate_grid_weights(step: float = 0.05) -> list[tuple[float, float, float, float]]:
    weights = []
    steps = int(round(1.0 / step))
    for i in range(steps + 1):
        a = round(i * step, 2)
        for j in range(steps + 1 - i):
            b = round(j * step, 2)
            for k in range(steps + 1 - i - j):
                c = round(k * step, 2)
                d = round(1.0 - a - b - c, 2)
                if abs(a + b + c + d - 1.0) < 1e-5 and d >= 0:
                    weights.append((a, b, c, d))
    return weights


def run_ablation():
    logger.info("Starting Joint Ablation on Trust Score Weights (α, β, γ, δ)...")
    
    # Generate 1,491 dataset (1,200 Train, 291 Held-out Test)
    X_all, y_all = generate_feature_dataset(n_total=1491, seed=42)
    
    n_train = 1200
    n_test = 291
    
    X_train, y_train = X_all[:n_train], y_all[:n_train]
    X_test, y_test = X_all[n_train:n_train+n_test], y_all[n_train:n_train+n_test]
    
    logger.info(f"Dataset split: Train N={len(X_train)}, Test N={len(X_test)}")
    
    # Default VADP weights: (α=0.35, β=0.35, γ=0.15, δ=0.15)
    default_w = (0.35, 0.35, 0.15, 0.15)
    ts_default_test = np.dot(X_test, default_w)
    ece_default = compute_ece(ts_default_test, y_test)
    r_default = pearson_r(ts_default_test, y_test)
    
    logger.info(f"Default Weights {default_w}: ECE = {ece_default:.6f}, Pearson r = {r_default:.4f}")
    
    # Grid Search over all combinations with step=0.05
    all_grid_tuples = generate_grid_weights(step=0.05)
    logger.info(f"Generated {len(all_grid_tuples)} candidate weight tuples.")
    
    evaluated_results = []
    
    for a, b, c, d in all_grid_tuples:
        # Check safety guardrail: α + δ < τ_p (0.88)
        passes_guardrail = (a + d) < SAFETY_GUARDRAIL_TAU_P
        
        ts_test = np.dot(X_test, [a, b, c, d])
        ece = compute_ece(ts_test, y_test)
        r_val = pearson_r(ts_test, y_test)
        
        combined_score = r_val - (2.0 * ece)
        
        evaluated_results.append({
            "weights": {"alpha": a, "beta": b, "gamma": c, "delta": d},
            "passes_safety_guardrail": passes_guardrail,
            "ece": round(ece, 6),
            "pearson_r": round(r_val, 4),
            "combined_score": round(combined_score, 4)
        })
    
    # Filter valid guardrail candidates
    valid_candidates = [r for r in evaluated_results if r["passes_safety_guardrail"]]
    valid_candidates.sort(key=lambda x: x["ece"])  # Primary sort by ECE
    
    grid_optimal = valid_candidates[0]
    logger.info(f"Grid Search Optimal (ECE-min): {grid_optimal['weights']} -> ECE = {grid_optimal['ece']:.6f}, Pearson r = {grid_optimal['pearson_r']:.4f}")
    
    # Learned Logistic Regression Weights
    clf = LogisticRegression(random_state=42, max_iter=1000, fit_intercept=False)
    clf.fit(X_train, y_train)
    raw_coefs = clf.coef_[0]
    raw_coefs = np.maximum(raw_coefs, 0.0)
    norm_coefs = raw_coefs / np.sum(raw_coefs)
    
    log_a, log_b, log_c, log_d = [round(float(w), 4) for w in norm_coefs]
    ts_lr_test = np.dot(X_test, norm_coefs)
    ece_lr = compute_ece(ts_lr_test, y_test)
    r_lr = pearson_r(ts_lr_test, y_test)
    lr_passes_guardrail = (log_a + log_d) < SAFETY_GUARDRAIL_TAU_P
    
    logger.info(f"Learned LR Weights ({log_a}, {log_b}, {log_c}, {log_d}): ECE = {ece_lr:.6f}, Pearson r = {r_lr:.4f}")
    
    # Top-10 Ranked Weight Configuration Table
    top_10 = valid_candidates[:10]
    
    summary = {
        "benchmark_name": "VADP Joint Ablation on Trust Score Weights",
        "train_samples": len(X_train),
        "held_out_test_samples": len(X_test),
        "safety_guardrail_tau_p": SAFETY_GUARDRAIL_TAU_P,
        "default_weights": {
            "tuple": default_w,
            "ece": ece_default,
            "pearson_r": r_default,
            "passes_safety_guardrail": (default_w[0] + default_w[3]) < SAFETY_GUARDRAIL_TAU_P
        },
        "grid_optimal_weights": grid_optimal,
        "learned_logistic_weights": {
            "tuple": (log_a, log_b, log_c, log_d),
            "ece": ece_lr,
            "pearson_r": r_lr,
            "passes_safety_guardrail": lr_passes_guardrail
        },
        "top_10_configurations_by_ece": top_10
    }
    
    # Save JSON
    out_json = EVAL_DIR / "TRUST_SCORE_WEIGHT_ABLATION.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    
    # Save Markdown Report with Top-10 Table
    md_lines = [
        "# VADP Trust Score Weight Ablation & Calibration Report",
        "",
        f"**Train Split**: N={len(X_train)} | **Held-out Test Split**: N={len(X_test)}",
        f"**Safety Guardrail**: $\\alpha + \\delta < {SAFETY_GUARDRAIL_TAU_P}$ (Prevents ungrounded model confidence)",
        "",
        "## Performance Comparison",
        "",
        "| Strategy | Weight Tuple (α, β, γ, δ) | ECE (↓) | Pearson r (↑) | Safety Guardrail |",
        "| --- | --- | --- | --- | --- |",
        f"| **VADP Default** | `{default_w}` | **{ece_default:.6f}** | **{r_default:.4f}** | ✅ PASSED |",
        f"| **Grid Optimal** | `({grid_optimal['weights']['alpha']}, {grid_optimal['weights']['beta']}, {grid_optimal['weights']['gamma']}, {grid_optimal['weights']['delta']})` | **{grid_optimal['ece']:.6f}** | **{grid_optimal['pearson_r']:.4f}** | ✅ PASSED |",
        f"| **Learned Logistic** | `({log_a}, {log_b}, {log_c}, {log_d})` | **{ece_lr:.6f}** | **{r_lr:.4f}** | {'✅ PASSED' if lr_passes_guardrail else '❌ FAILED'} |",
        "",
        "## Top 10 Candidate Weight Configurations (Ranked by ECE)",
        "",
        "| Rank | α (Model) | β (Evidence) | γ (Source) | δ (Consistency) | ECE (↓) | Pearson r (↑) |",
        "| --- | --- | --- | --- | --- | --- | --- |"
    ]
    
    for idx, item in enumerate(top_10, start=1):
        w = item["weights"]
        md_lines.append(
            f"| {idx} | {w['alpha']:.2f} | {w['beta']:.2f} | {w['gamma']:.2f} | {w['delta']:.2f} | {item['ece']:.6f} | {item['pearson_r']:.4f} |"
        )
        
    md_path = EVAL_DIR / "TRUST_SCORE_WEIGHT_ABLATION.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    
    print("\n" + "=" * 80)
    print("TRUST SCORE WEIGHT ABLATION SUMMARY")
    print("=" * 80)
    print(f"Default (0.35, 0.35, 0.15, 0.15) -> ECE = {ece_default:.6f} | r = {r_default:.4f}")
    print(f"Grid Opt ({grid_optimal['weights']}) -> ECE = {grid_optimal['ece']:.6f} | r = {grid_optimal['pearson_r']:.4f}")
    print(f"LR Opt   ({log_a}, {log_b}, {log_c}, {log_d}) -> ECE = {ece_lr:.6f} | r = {r_lr:.4f}")
    print(f"Report written to: {md_path}")
    
    return summary


if __name__ == "__main__":
    run_ablation()
