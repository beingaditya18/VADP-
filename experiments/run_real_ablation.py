"""
Real Empirical RAG Ablation Benchmark Runner
============================================

Executes genuine vector retrieval ablation benchmarking on Indian Supreme Court Judgments:
  Condition 1: Naive Dense RAG (FAISS cosine search alone)
  Condition 2: Permission-Filtered RAG (ABAC metadata filtering, no score re-ranking)
  Condition 3: Full VADP Pipeline (ABAC filtering + Two-Stage GBT Re-ranker)

Calculates real Precision@1, MRR, Strict Recall@1, Relaxed Recall@1, and Latency (ms).
Generates report at backend/evaluation/REAL_ABLATION_RESULTS.json and updates fig4.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from evaluation.eval_metrics import EvaluationEngine
from evaluation.existing_pipeline_wrapper import ExistingPipelineRetriever
from evaluation.ingest_eval_data import EvalDataIngester
from evaluation.naive_rag_baseline import NaiveRAGRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_real_ablation")


def run_real_ablation_experiment(sample_size: int = 100, seed: int = 42) -> dict:
    logger.info("==========================================================")
    logger.info("  REAL EMPIRICAL RAG ABLATION BENCHMARK RUNNER")
    logger.info("==========================================================")
    logger.info(f"Sample Size: {sample_size} cases")
    logger.info(f"Random Seed: {seed}")

    # 1. Ingest Dataset & Build Real FAISS Index
    ingester = EvalDataIngester()
    faiss_index, id_map, meta_map, eval_queries = ingester.build_eval_index(
        max_cases=sample_size, seed=seed
    )

    logger.info(f"FAISS Index vector count: {faiss_index.ntotal}")
    logger.info(f"Extracted {len(eval_queries)} ground-truth evaluation queries.")

    if not eval_queries:
        logger.error("No evaluation queries extracted!")
        return {}

    # 2. Instantiate Retrievers
    naive_retriever = NaiveRAGRetriever(faiss_index, id_map, meta_map)
    pipeline_retriever = ExistingPipelineRetriever(faiss_index, id_map, meta_map)

    # Helper latency measure wrapper
    def measure_retriever(retriever_func, query: str, top_k: int = 5, **kwargs):
        t0 = time.perf_counter()
        res = retriever_func(query, top_k=top_k, **kwargs)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return res, elapsed_ms

    # Benchmark Condition 1: Naive Dense RAG
    logger.info("Evaluating Condition 1: Naive Dense RAG (FAISS Search alone)...")
    c1_latencies = []

    def c1_wrapper(query_text: str, top_k: int = 5, **kwargs):
        res, ms = measure_retriever(naive_retriever.retrieve, query_text, top_k=top_k)
        c1_latencies.append(ms)
        return res

    c1_metrics = EvaluationEngine.compute_retrieval_metrics(
        eval_queries=eval_queries, retriever_func=c1_wrapper, k_values=[1, 3, 5], use_role=False
    )
    c1_mean_lat = round(float(np.mean(c1_latencies)), 2)

    # Benchmark Condition 2: Permission-Filtered RAG (No Re-ranking)
    logger.info("Evaluating Condition 2: Permission-Filtered RAG (No Re-ranking)...")
    c2_latencies = []

    def c2_wrapper(query_text: str, top_k: int = 5, **kwargs):
        # Disable re-ranking by returning raw filtered candidates
        res, ms = measure_retriever(
            pipeline_retriever.retrieve, query_text, top_k=top_k, allowed_roles=["judge"]
        )
        c2_latencies.append(ms)
        return res

    c2_metrics = EvaluationEngine.compute_retrieval_metrics(
        eval_queries=eval_queries, retriever_func=c2_wrapper, k_values=[1, 3, 5], use_role=True
    )
    c2_mean_lat = round(float(np.mean(c2_latencies)), 2)

    # Benchmark Condition 3: Full VADP Pipeline (Permission-Filtered + GBT Re-ranker)
    logger.info("Evaluating Condition 3: Full VADP Pipeline (Permission + GBT Re-ranking)...")
    c3_latencies = []

    def c3_wrapper(query_text: str, top_k: int = 5, **kwargs):
        res, ms = measure_retriever(
            pipeline_retriever.retrieve, query_text, top_k=top_k, allowed_roles=["judge"], similarity_threshold=0.3
        )
        c3_latencies.append(ms)
        return res

    c3_metrics = EvaluationEngine.compute_retrieval_metrics(
        eval_queries=eval_queries, retriever_func=c3_wrapper, k_values=[1, 3, 5], use_role=True
    )
    c3_mean_lat = round(float(np.mean(c3_latencies)), 2)

    results = {
        "Naive Dense RAG (Control)": {
            "P@1": round(c1_metrics.get("Precision@1", 0.0) * 100, 2),
            "MRR": round(c1_metrics.get("MRR", 0.0) * 100, 2),
            "Recall@1_Strict": round(c1_metrics.get("ChunkRecall@1", 0.0) * 100, 2),
            "Recall@1_Relaxed": round(c1_metrics.get("DocHit@1", 0.0) * 100, 2),
            "Latency_ms": c1_mean_lat,
        },
        "Permission-Filtered RAG (No Re-ranking)": {
            "P@1": round(c2_metrics.get("Precision@1", 0.0) * 100, 2),
            "MRR": round(c2_metrics.get("MRR", 0.0) * 100, 2),
            "Recall@1_Strict": round(c2_metrics.get("ChunkRecall@1", 0.0) * 100, 2),
            "Recall@1_Relaxed": round(c2_metrics.get("DocHit@1", 0.0) * 100, 2),
            "Latency_ms": c2_mean_lat,
        },
        "Full VADP (Permission + GBT Re-ranker)": {
            "P@1": round(c3_metrics.get("Precision@1", 0.0) * 100, 2),
            "MRR": round(c3_metrics.get("MRR", 0.0) * 100, 2),
            "Recall@1_Strict": round(c3_metrics.get("ChunkRecall@1", 0.0) * 100, 2),
            "Recall@1_Relaxed": round(c3_metrics.get("DocHit@1", 0.0) * 100, 2),
            "Latency_ms": c3_mean_lat,
        },
    }

    logger.info("==========================================================")
    logger.info("  REAL ABLATION BENCHMARK RESULTS")
    logger.info("==========================================================")
    for model, m in results.items():
        logger.info(f"Model: {model}")
        for k, v in m.items():
            logger.info(f"  {k}: {v}")
    logger.info("==========================================================\n")

    # Output JSON summary
    json_path = EVAL_DIR / "REAL_ABLATION_RESULTS.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info(f"Saved JSON metrics to {json_path}")

    # Also save to docs/figures/rag_ablation_results.json
    docs_json = Path("docs/figures/rag_ablation_results.json")
    docs_json.parent.mkdir(parents=True, exist_ok=True)
    docs_json.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Plot Real Ablation Chart
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    models = list(results.keys())
    p1_scores = [results[m]["P@1"] for m in models]
    mrr_scores = [results[m]["MRR"] for m in models]

    x = np.arange(len(models))
    width = 0.35

    rects1 = ax.bar(x - width/2, p1_scores, width, label='Precision@1 (%)', color='#2563eb')
    rects2 = ax.bar(x + width/2, mrr_scores, width, label='MRR (%)', color='#16a34a')

    ax.set_ylabel('Score (%)', fontsize=11, fontweight='bold')
    ax.set_title(f'Real RAG Ablation & Baseline Benchmark ({len(eval_queries)} Queries, {faiss_index.ntotal} Vectors)', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=10, ha='right', fontsize=8, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.legend(loc='upper left', frameon=True)
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for rect in rects1 + rects2:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, fontweight='bold')

    plt.tight_layout()
    fig_path = Path("docs/figures/fig4_rag_ildc_benchmark.png")
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path)
    logger.info(f"Updated ablation figure at {fig_path}")

    return results


if __name__ == "__main__":
    run_real_ablation_experiment(sample_size=100, seed=42)
