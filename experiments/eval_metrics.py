"""
Evaluation Harness: Retrieval Metrics & Trust Score Calibration Module (Corrected)
===================================================================================

Computes:
  1. Retrieval Metrics:
     - Precision@K (K=1, 3, 5)
     - Primary-Chunk Recall@K (K=1, 3, 5) using primary ground-truth chunks (denominator = |R_primary|)
     - Document Hit Rate@K (Hit@K) measuring target case retrieval
     - Mean Reciprocal Rank (MRR)
  2. Trust Score Calibration:
     - Full dataset correlation (N_full, Pearson r, Spearman rho, R^2, ECE)
     - Active subset sensitivity correlation (N_active, Pearson r, Spearman rho)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.trust_engine import TrustScoringEngine

logger = logging.getLogger("eval_harness.metrics")


class EvaluationEngine:
    """Computes retrieval evaluation metrics and Trust Score calibration statistics."""

    @staticmethod
    def compute_retrieval_metrics(
        eval_queries: list[dict[str, Any]],
        retriever_func,
        k_values: list[int] = [1, 3, 5],
        use_role: bool = True,
        use_case_boundary: bool = False,
        **retriever_kwargs,
    ) -> dict[str, float]:
        """
        Evaluate a retriever over a list of query dicts.

        Metrics computed:
            - Precision@K: fraction of retrieved top-K chunks that match target case/topic
            - Primary-Chunk-Recall@K: fraction of primary target chunks retrieved (denominator = |R_primary|)
            - Document-Hit@K: whether the target case document is in top-K
            - MRR: Mean Reciprocal Rank of first target hit
        """
        precisions = {k: [] for k in k_values}
        primary_recalls = {k: [] for k in k_values}
        doc_hits = {k: [] for k in k_values}
        reciprocal_ranks = []

        max_k = max(k_values)

        for q in eval_queries:
            query_text = q["query_text"]
            primary_chunks = q.get("primary_relevant_chunk_ids", q["relevant_chunk_ids"])
            target_case_id = q["relevant_case_id"]
            num_primary = len(primary_chunks)

            # Optional ABAC & Case Isolation parameters
            kwargs = dict(retriever_kwargs)
            if use_role and "required_role" in q:
                kwargs["allowed_roles"] = [q["required_role"]]
            if use_case_boundary:
                kwargs["allowed_case_id"] = target_case_id

            results = retriever_func(query_text=query_text, top_k=max_k, **kwargs)
            retrieved_chunk_ids = [r[0] for r in results]
            retrieved_case_ids = [r[2].get("case_id") for r in results if len(r) > 2]

            # MRR (first primary or case hit)
            first_rank = 0
            for rank_idx, cid in enumerate(retrieved_chunk_ids, start=1):
                if cid in primary_chunks or (rank_idx <= len(retrieved_case_ids) and retrieved_case_ids[rank_idx - 1] == target_case_id):
                    first_rank = rank_idx
                    break
            rr = 1.0 / first_rank if first_rank > 0 else 0.0
            reciprocal_ranks.append(rr)

            # P@K, Recall@K, and Hit@K
            for k in k_values:
                top_k_retrieved = retrieved_chunk_ids[:k]
                top_k_cases = retrieved_case_ids[:k]

                # Hits against primary chunks
                primary_hits = sum(1 for cid in top_k_retrieved if cid in primary_chunks)
                case_hits = sum(1 for cid in top_k_retrieved if cid in q["relevant_chunk_ids"])

                pk = case_hits / float(k) if k > 0 else 0.0
                rk = primary_hits / float(num_primary) if num_primary > 0 else 0.0
                hit = 1.0 if target_case_id in top_k_cases or primary_hits > 0 else 0.0

                precisions[k].append(pk)
                primary_recalls[k].append(rk)
                doc_hits[k].append(hit)

        metrics = {}
        for k in k_values:
            metrics[f"Precision@{k}"] = round(float(np.mean(precisions[k])), 4)
            metrics[f"ChunkRecall@{k}"] = round(float(np.mean(primary_recalls[k])), 4)
            metrics[f"DocHit@{k}"] = round(float(np.mean(doc_hits[k])), 4)

        metrics["MRR"] = round(float(np.mean(reciprocal_ranks)), 4)
        return metrics

    @staticmethod
    def evaluate_trust_calibration(
        eval_queries: list[dict[str, Any]],
        pipeline_retriever_func,
        top_k: int = 5,
        use_role: bool = True,
    ) -> dict[str, Any]:
        """
        Compute Trust Score calibration and sensitivity statistics.
        """
        trust_scores = []
        ground_truth_relevance = []

        for q in eval_queries:
            query_text = q["query_text"]
            relevant_chunks = q["relevant_chunk_ids"]

            kwargs = {}
            if use_role and "required_role" in q:
                kwargs["allowed_roles"] = [q["required_role"]]

            results = pipeline_retriever_func(query_text=query_text, top_k=top_k, **kwargs)

            if not results:
                trust_breakdown = TrustScoringEngine.calculate_trust_score(
                    model_confidence=0.0, evidence_quality=0.0
                )
                trust_scores.append(trust_breakdown.overall)
                ground_truth_relevance.append(0.0)
                continue

            top_sim = results[0][1]
            hits = sum(1 for cid, score, meta in results if cid in relevant_chunks or meta.get("case_id") == q["relevant_case_id"])

            model_conf = max(0.0, min(1.0, float(top_sim)))
            evidence_qual = hits / float(len(results))

            trust_res = TrustScoringEngine.calculate_trust_score(
                model_confidence=model_conf,
                evidence_quality=evidence_qual,
                source_reliability=0.90,
                consistency=0.88 if hits > 0 else 0.40,
            )

            gt_signal = evidence_qual

            trust_scores.append(trust_res.overall)
            ground_truth_relevance.append(gt_signal)

        ts_arr = np.array(trust_scores, dtype=np.float64)
        gt_arr = np.array(ground_truth_relevance, dtype=np.float64)

        n_full = len(ts_arr)

        # Full sample correlation
        if n_full > 1 and np.std(ts_arr) > 0 and np.std(gt_arr) > 0:
            pearson_r, pearson_p = stats.pearsonr(ts_arr, gt_arr)
            spearman_rho, spearman_p = stats.spearmanr(ts_arr, gt_arr)
            slope, intercept, r_value, p_val, std_err = stats.linregress(ts_arr, gt_arr)
            r_squared = r_value ** 2
        else:
            pearson_r, pearson_p = 0.0, 1.0
            spearman_rho, spearman_p = 0.0, 1.0
            r_squared = 0.0

        # Sensitivity check: Active subset (excluding zero-hit / blocked queries)
        active_mask = gt_arr > 0
        n_active = int(np.sum(active_mask))
        if n_active > 1 and np.std(ts_arr[active_mask]) > 0 and np.std(gt_arr[active_mask]) > 0:
            act_pearson_r, act_pearson_p = stats.pearsonr(ts_arr[active_mask], gt_arr[active_mask])
            act_spearman_rho, act_spearman_p = stats.spearmanr(ts_arr[active_mask], gt_arr[active_mask])
        else:
            act_pearson_r, act_pearson_p = pearson_r, pearson_p
            act_spearman_rho, act_spearman_p = spearman_rho, spearman_p

        # Expected Calibration Error (ECE)
        bins = np.linspace(0.0, 1.0, 6)
        ece = 0.0
        bin_details = []
        for i in range(len(bins) - 1):
            bin_lower = bins[i]
            bin_upper = bins[i + 1]

            if i == len(bins) - 2:
                in_bin = (ts_arr >= bin_lower) & (ts_arr <= bin_upper)
            else:
                in_bin = (ts_arr >= bin_lower) & (ts_arr < bin_upper)

            bin_size = np.sum(in_bin)
            if bin_size > 0:
                avg_conf = np.mean(ts_arr[in_bin])
                avg_acc = np.mean(gt_arr[in_bin])
                gap = abs(avg_conf - avg_acc)
                ece += (bin_size / float(n_full)) * gap

                bin_details.append({
                    "bin_range": f"[{bin_lower:.1f}, {bin_upper:.1f}]",
                    "sample_count": int(bin_size),
                    "avg_trust_score": round(float(avg_conf), 4),
                    "avg_gt_relevance": round(float(avg_acc), 4),
                    "calibration_gap": round(float(gap), 4),
                })

        return {
            "n_full": n_full,
            "n_active": n_active,
            "pearson_r": round(float(pearson_r), 4),
            "pearson_p_value": float(pearson_p),
            "spearman_rho": round(float(spearman_rho), 4),
            "spearman_p_value": float(spearman_p),
            "r_squared": round(float(r_squared), 4),
            "active_pearson_r": round(float(act_pearson_r), 4),
            "active_spearman_rho": round(float(act_spearman_rho), 4),
            "expected_calibration_error": round(float(ece), 4),
            "mean_trust_score": round(float(np.mean(ts_arr)), 4),
            "mean_gt_relevance": round(float(np.mean(gt_arr)), 4),
            "bin_details": bin_details,
            "raw_pairs": list(zip([round(float(t), 4) for t in ts_arr], [round(float(g), 4) for g in gt_arr])),
        }
