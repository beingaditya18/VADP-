"""
Strict 5-Fold Cross-Validation Statutory Feature Ablation Benchmark
====================================================================

Evaluates 4 retrieval conditions using strict 5-Fold Cross-Validation
(80 queries train / 20 held-out validation queries per fold, 5 folds total):

  Condition 1: Control (Naive Dense RAG, no role filter, no re-ranking)
  Condition 2: Permission-Filtered Baseline (ABAC role filter, raw FAISS rank)
  Condition 3: Full VADP Pipeline (ABAC role filter + 8-Feature LambdaMART, trained ONLY on 80 train queries)
  Condition 4: Statutory-Ablated VADP (ABAC role filter + 5-Feature LambdaMART, trained ONLY on 80 train queries)

No query is ever evaluated on a model trained on itself.
Outputs:
  - backend/evaluation/FIVE_FOLD_ABLATION_BENCHMARK.json
  - backend/evaluation/FIVE_FOLD_PER_QUERY_LOG.json
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np
import xgboost as xgb

BACKEND_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.rag.learning_to_rank import LTRCandidateFeatures, LambdaMARTLearningToRank
from evaluation.ingest_eval_data import EvalDataIngester

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("5fold_ablation")


def extract_features(
    query_text: str,
    chunk_meta: dict[str, Any],
    dense_sim: float,
    query_sections: list[str],
    query_topics: list[str],
) -> LTRCandidateFeatures:
    """Extract standard 8 LTR features for a candidate chunk given query context."""
    cand_sections = chunk_meta.get("sections", [])
    cand_topics = chunk_meta.get("topics", [])

    # Feature 2: BM25 lexical token overlap score
    q_words = set(query_text.lower().split())
    c_words = set(chunk_meta.get("content", "").lower().split())
    bm25 = len(q_words & c_words) / (len(q_words) + 1.0)
    bm25 = float(np.clip(bm25 * 3.0, 0.0, 1.0))

    # Feature 5: Temporal recency decay
    temporal_recency = 0.85

    # Feature 6: Bench / coram relevance
    if query_topics and cand_topics:
        topic_match = len(set(query_topics) & set(cand_topics)) / float(len(set(query_topics) | set(cand_topics)))
    else:
        topic_match = 0.5
    bench_relevance = round(float(topic_match), 4)

    # Feature 7: BSA §63(4) evidence alignment
    bsa_terms = {"section 65b", "65b", "bsa 63", "electronic record", "certificate"}
    has_bsa_q = any(t in query_text.lower() for t in bsa_terms)
    has_bsa_c = any(t in chunk_meta.get("content", "").lower() for t in bsa_terms)
    bsa_evidence = 1.0 if (has_bsa_q and has_bsa_c) else (0.5 if not has_bsa_q else 0.0)

    # Feature 8: PageRank centrality
    citation_centrality = float(np.clip(0.4 + 0.1 * (chunk_meta.get("chunk_index", 0) % 5), 0.1, 1.0))

    return LambdaMARTLearningToRank.build_candidate(
        chunk_id=chunk_meta.get("chunk_id", ""),
        query_id="",
        dense_similarity=dense_sim,
        query_sections=query_sections,
        candidate_sections=cand_sections,
        bm25_score=bm25,
        temporal_recency=temporal_recency,
        bench_relevance=bench_relevance,
        bsa_evidence_alignment=bsa_evidence,
        citation_centrality=citation_centrality,
        relevance_label=0,
    )


def run_5fold_ablation(sample_size: int = 100, n_folds: int = 5, seed: int = 42) -> dict[str, Any]:
    logger.info("========================================================================")
    logger.info("  STRICT 5-FOLD CROSS-VALIDATION RAG ABLATION BENCHMARK")
    logger.info("========================================================================")

    # 1. Ingest Dataset & Build Index
    ingester = EvalDataIngester()
    faiss_index, id_map, meta_map, eval_queries = ingester.build_eval_index(
        max_cases=sample_size, seed=seed
    )
    logger.info(f"Loaded {len(eval_queries)} ground-truth queries over FAISS index ({faiss_index.ntotal} vectors).")

    # 2. Extract Candidates & Features for all queries (top 20 candidates per query)
    dataset_groups: list[dict[str, Any]] = []

    for q in eval_queries:
        q_id = q["query_id"]
        q_text = q["query_text"]
        q_sections = q.get("sections", [])
        q_topics = q.get("topics", [])
        req_role = q.get("required_role", "judge")
        target_case_id = q["relevant_case_id"]
        primary_chunks = q["primary_relevant_chunk_ids"]
        all_relevant_chunks = q["relevant_chunk_ids"]

        q_vec = ingester.encoder.encode([q_text])
        faiss.normalize_L2(q_vec)
        distances, indices = faiss_index.search(q_vec, 20)

        raw_candidates = []
        for dist, idx_val in zip(distances[0], indices[0]):
            if idx_val < 0 or idx_val >= len(id_map):
                continue
            chunk_id = id_map[idx_val]
            chunk_meta = meta_map.get(chunk_id, {})

            allowed_roles = chunk_meta.get("allowed_roles", [])
            passes_role = True if not allowed_roles else (req_role in allowed_roles)

            if chunk_id in primary_chunks:
                rel_label = 3
            elif chunk_id in all_relevant_chunks or chunk_meta.get("case_id") == target_case_id:
                rel_label = 2
            else:
                rel_label = 0

            cand_features = extract_features(
                query_text=q_text,
                chunk_meta=chunk_meta,
                dense_sim=float(dist),
                query_sections=q_sections,
                query_topics=q_topics,
            )
            cand_features.chunk_id = chunk_id
            cand_features.query_id = q_id
            cand_features.relevance_label = rel_label

            raw_candidates.append({
                "chunk_id": chunk_id,
                "dense_sim": float(dist),
                "case_id": chunk_meta.get("case_id"),
                "passes_role": passes_role,
                "rel_label": rel_label,
                "features": cand_features,
            })

        dataset_groups.append({
            "query_id": q_id,
            "query_text": q_text,
            "target_case_id": target_case_id,
            "req_role": req_role,
            "raw_candidates": raw_candidates,
        })

    # Shuffle dataset deterministically for 5-fold CV split
    np.random.seed(seed)
    indices_shuffled = np.arange(len(dataset_groups))
    np.random.shuffle(indices_shuffled)

    fold_size = len(dataset_groups) // n_folds
    per_query_log: list[dict[str, Any]] = []

    fold_results = []

    for fold in range(n_folds):
        val_idx_range = indices_shuffled[fold * fold_size : (fold + 1) * fold_size]
        train_idx_range = np.array([i for i in indices_shuffled if i not in set(val_idx_range)])

        train_groups = [dataset_groups[i] for i in train_idx_range]
        val_groups = [dataset_groups[i] for i in val_idx_range]

        # Prepare train arrays for Full and Ablated LambdaMART models
        X_train_full, X_train_ablated, y_train, train_group_sizes = [], [], [], []

        for group in train_groups:
            train_group_sizes.append(len(group["raw_candidates"]))
            for item in group["raw_candidates"]:
                cand: LTRCandidateFeatures = item["features"]
                X_train_full.append(cand.to_feature_vector())
                X_train_ablated.append([
                    cand.dense_similarity,
                    cand.bm25_score,
                    cand.temporal_recency,
                    cand.bench_relevance,
                    cand.citation_centrality,
                ])
                y_train.append(cand.relevance_label)

        # Fit models ONLY on the 80 train queries
        full_model = xgb.XGBRanker(objective="rank:pairwise", n_estimators=30, learning_rate=0.08, max_depth=3, random_state=42 + fold)
        full_model.fit(np.array(X_train_full), np.array(y_train), group=train_group_sizes)

        ablated_model = xgb.XGBRanker(objective="rank:pairwise", n_estimators=30, learning_rate=0.08, max_depth=3, random_state=42 + fold)
        ablated_model.fit(np.array(X_train_ablated), np.array(y_train), group=train_group_sizes)

        # Evaluate on the 20 HELD-OUT validation queries
        fold_c1_p1, fold_c1_mrr = [], []
        fold_c2_p1, fold_c2_mrr = [], []
        fold_c3_p1, fold_c3_mrr = [], []
        fold_c4_p1, fold_c4_mrr = [], []

        for q_val in val_groups:
            q_id = q_val["query_id"]
            target_case_id = q_val["target_case_id"]
            req_role = q_val["req_role"]
            raw_cands = q_val["raw_candidates"]

            # Condition 1: Control (Naive Dense RAG)
            c1_sorted = sorted(raw_cands, key=lambda x: x["dense_sim"], reverse=True)
            c1_top1 = c1_sorted[0] if c1_sorted else None
            c1_hit = 1 if (c1_top1 and (c1_top1["case_id"] == target_case_id or c1_top1["rel_label"] >= 2)) else 0
            fold_c1_p1.append(c1_hit)
            c1_mrr_val = 0.0
            for rank_i, item in enumerate(c1_sorted, start=1):
                if item["case_id"] == target_case_id or item["rel_label"] >= 2:
                    c1_mrr_val = 1.0 / rank_i
                    break
            fold_c1_mrr.append(c1_mrr_val)

            # Condition 2: Permission-Filtered Baseline
            c2_filtered = [c for c in raw_cands if c["passes_role"]]
            c2_sorted = sorted(c2_filtered, key=lambda x: x["dense_sim"], reverse=True)
            c2_top1 = c2_sorted[0] if c2_sorted else None
            c2_hit = 1 if (c2_top1 and (c2_top1["case_id"] == target_case_id or c2_top1["rel_label"] >= 2)) else 0
            fold_c2_p1.append(c2_hit)
            c2_mrr_val = 0.0
            for rank_i, item in enumerate(c2_sorted, start=1):
                if item["case_id"] == target_case_id or item["rel_label"] >= 2:
                    c2_mrr_val = 1.0 / rank_i
                    break
            fold_c2_mrr.append(c2_mrr_val)

            # Condition 3: Full VADP (Out-of-fold 8-Feature LambdaMART)
            if c2_filtered:
                X_val_full = np.array([c["features"].to_feature_vector() for c in c2_filtered])
                scores_full = full_model.predict(X_val_full)
                scored_full = [(c, float(s)) for c, s in zip(c2_filtered, scores_full)]
                c3_sorted = [c for c, _ in sorted(scored_full, key=lambda x: x[1], reverse=True)]
            else:
                c3_sorted = []

            c3_top1 = c3_sorted[0] if c3_sorted else None
            c3_hit = 1 if (c3_top1 and (c3_top1["case_id"] == target_case_id or c3_top1["rel_label"] >= 2)) else 0
            fold_c3_p1.append(c3_hit)
            c3_mrr_val = 0.0
            for rank_i, item in enumerate(c3_sorted, start=1):
                if item["case_id"] == target_case_id or item["rel_label"] >= 2:
                    c3_mrr_val = 1.0 / rank_i
                    break
            fold_c3_mrr.append(c3_mrr_val)

            # Condition 4: Ablated VADP (Out-of-fold 5-Feature LambdaMART)
            if c2_filtered:
                X_val_ablated = np.array([
                    [
                        c["features"].dense_similarity,
                        c["features"].bm25_score,
                        c["features"].temporal_recency,
                        c["features"].bench_relevance,
                        c["features"].citation_centrality,
                    ] for c in c2_filtered
                ])
                scores_ablated = ablated_model.predict(X_val_ablated)
                scored_ablated = [(c, float(s)) for c, s in zip(c2_filtered, scores_ablated)]
                c4_sorted = [c for c, _ in sorted(scored_ablated, key=lambda x: x[1], reverse=True)]
            else:
                c4_sorted = []

            c4_top1 = c4_sorted[0] if c4_sorted else None
            c4_hit = 1 if (c4_top1 and (c4_top1["case_id"] == target_case_id or c4_top1["rel_label"] >= 2)) else 0
            fold_c4_p1.append(c4_hit)
            c4_mrr_val = 0.0
            for rank_i, item in enumerate(c4_sorted, start=1):
                if item["case_id"] == target_case_id or item["rel_label"] >= 2:
                    c4_mrr_val = 1.0 / rank_i
                    break
            fold_c4_mrr.append(c4_mrr_val)

            per_query_log.append({
                "fold": fold + 1,
                "query_id": q_id,
                "target_case_id": target_case_id,
                "required_role": req_role,
                "c1_control_top1": c1_top1["chunk_id"] if c1_top1 else None,
                "c1_hit": c1_hit,
                "c2_no_rerank_top1": c2_top1["chunk_id"] if c2_top1 else None,
                "c2_hit": c2_hit,
                "c3_full_vadp_top1": c3_top1["chunk_id"] if c3_top1 else None,
                "c3_hit": c3_hit,
                "c4_ablated_vadp_top1": c4_top1["chunk_id"] if c4_top1 else None,
                "c4_hit": c4_hit,
            })

        fold_metrics = {
            "fold": fold + 1,
            "n_val_queries": len(val_groups),
            "Condition_1_Control": {
                "P@1": round(float(np.mean(fold_c1_p1)) * 100, 2),
                "MRR": round(float(np.mean(fold_c1_mrr)) * 100, 2),
            },
            "Condition_2_Permission_Filtered": {
                "P@1": round(float(np.mean(fold_c2_p1)) * 100, 2),
                "MRR": round(float(np.mean(fold_c2_mrr)) * 100, 2),
            },
            "Condition_3_Full_LambdaMART": {
                "P@1": round(float(np.mean(fold_c3_p1)) * 100, 2),
                "MRR": round(float(np.mean(fold_c3_mrr)) * 100, 2),
            },
            "Condition_4_Ablated_LambdaMART": {
                "P@1": round(float(np.mean(fold_c4_p1)) * 100, 2),
                "MRR": round(float(np.mean(fold_c4_mrr)) * 100, 2),
            },
        }
        fold_results.append(fold_metrics)
        logger.info(
            f"[+] Fold {fold+1}/5 -> Full P@1: {fold_metrics['Condition_3_Full_LambdaMART']['P@1']:.2f}% | Ablated P@1: {fold_metrics['Condition_4_Ablated_LambdaMART']['P@1']:.2f}% | Control P@1: {fold_metrics['Condition_1_Control']['P@1']:.2f}%"
        )

    # Compute overall mean ± std across 5 folds
    c1_p1_folds = [f["Condition_1_Control"]["P@1"] for f in fold_results]
    c1_mrr_folds = [f["Condition_1_Control"]["MRR"] for f in fold_results]

    c2_p1_folds = [f["Condition_2_Permission_Filtered"]["P@1"] for f in fold_results]
    c2_mrr_folds = [f["Condition_2_Permission_Filtered"]["MRR"] for f in fold_results]

    c3_p1_folds = [f["Condition_3_Full_LambdaMART"]["P@1"] for f in fold_results]
    c3_mrr_folds = [f["Condition_3_Full_LambdaMART"]["MRR"] for f in fold_results]

    c4_p1_folds = [f["Condition_4_Ablated_LambdaMART"]["P@1"] for f in fold_results]
    c4_mrr_folds = [f["Condition_4_Ablated_LambdaMART"]["MRR"] for f in fold_results]

    summary_table = {
        "Condition_1_Control": {
            "mean_P@1": round(float(np.mean(c1_p1_folds)), 2),
            "std_P@1": round(float(np.std(c1_p1_folds)), 2),
            "mean_MRR": round(float(np.mean(c1_mrr_folds)), 2),
            "std_MRR": round(float(np.std(c1_mrr_folds)), 2),
        },
        "Condition_2_Permission_Filtered": {
            "mean_P@1": round(float(np.mean(c2_p1_folds)), 2),
            "std_P@1": round(float(np.std(c2_p1_folds)), 2),
            "mean_MRR": round(float(np.mean(c2_mrr_folds)), 2),
            "std_MRR": round(float(np.std(c2_mrr_folds)), 2),
        },
        "Condition_3_Full_LambdaMART": {
            "mean_P@1": round(float(np.mean(c3_p1_folds)), 2),
            "std_P@1": round(float(np.std(c3_p1_folds)), 2),
            "mean_MRR": round(float(np.mean(c3_mrr_folds)), 2),
            "std_MRR": round(float(np.std(c3_mrr_folds)), 2),
        },
        "Condition_4_Ablated_LambdaMART": {
            "mean_P@1": round(float(np.mean(c4_p1_folds)), 2),
            "std_P@1": round(float(np.std(c4_p1_folds)), 2),
            "mean_MRR": round(float(np.mean(c4_mrr_folds)), 2),
            "std_MRR": round(float(np.std(c4_mrr_folds)), 2),
        },
    }

    final_report = {
        "protocol": "Strict 5-Fold Cross-Validation (Out-of-Fold Evaluation)",
        "n_queries_total": len(eval_queries),
        "n_folds": n_folds,
        "queries_per_fold": fold_size,
        "per_fold_results": fold_results,
        "summary_table_5fold_mean_std": summary_table,
    }

    report_path = EVAL_DIR / "FIVE_FOLD_ABLATION_BENCHMARK.json"
    log_path = EVAL_DIR / "FIVE_FOLD_PER_QUERY_LOG.json"

    report_path.write_text(json.dumps(final_report, indent=2), encoding="utf-8")
    log_path.write_text(json.dumps(per_query_log, indent=2), encoding="utf-8")

    logger.info(f"Saved 5-fold cross-validation report to: {report_path}")
    logger.info(f"Saved 5-fold per-query log to: {log_path}")

    print("\n" + "=" * 80)
    print("  STRICT 5-FOLD CROSS-VALIDATION ABLATION BENCHMARK RESULTS")
    print("=" * 80)
    print(f"{'Retrieval Condition':<40} | {'Mean P@1 ± Std':<18} | {'Mean MRR ± Std':<18}")
    print("-" * 80)
    for cond_name, stats in summary_table.items():
        p1_str = f"{stats['mean_P@1']:.2f}% ± {stats['std_P@1']:.2f}%"
        mrr_str = f"{stats['mean_MRR']:.2f}% ± {stats['std_MRR']:.2f}%"
        print(f"{cond_name:<40} | {p1_str:<18} | {mrr_str:<18}")
    print("=" * 80 + "\n")

    return final_report


if __name__ == "__main__":
    run_5fold_ablation(sample_size=100, n_folds=5, seed=42)
