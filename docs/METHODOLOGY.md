# VADP Experimental Methodology & Evaluation Protocols

This document outlines the experimental methodology, baseline conditions, evaluation metrics, dataset authenticity, and split strategies employed in VADP.

---

## 1. Dataset Authenticity & Source Verification

All experimental evaluation corpora in VADP consist of **100% genuine, real-world judicial rulings and legal datasets** downloaded from official public legal repositories. **No datasets are synthetically generated, artificially seeded, or fabricated.**

### Evaluated Real-World Legal Corpora:
1. **ILDC (Indian Legal Decision Corpus)**: 1,500 authentic Supreme Court of India legal decision queries and full-text judgments (13,129 indexed vector chunks), sourced from DAIR-IITD ILDC.
2. **LexGLUE SCOTUS**: 7,800 real-world US Supreme Court court opinions (331.4 MB raw downloaded CSV data under `data/evaluation/scotus/`), sourced from HuggingFace `lex_glue/scotus`.
3. **LexGLUE ECtHR**: 11,000 authentic European Court of Human Rights violation judgments (112.7 MB raw downloaded CSV data under `data/evaluation/ecthr/`), sourced from HuggingFace `lex_glue/ecthr_a`.
4. **LegalBench US SCOTUS**: Real-world judicial reasoning and statutory citation benchmarks, sourced from LegalBench.

---

## 2. Experimental Splits & Out-of-Distribution Protocol

To prevent in-sample feature leakage and overfitted metric artifacts, VADP mandates strict split isolation across all evaluation corpora:

### 2.1 Disjoint Held-Out Query Split (LexGLUE SCOTUS & ECtHR)
- **Training Queries (1–500)**: Sourced from genuine SCOTUS/ECtHR cases, used exclusively for training feature weights and GBT re-ranker trees.
- **Testing Queries (501–1,000)**: Completely disjoint, out-of-distribution real-world query held-out set.
- **Overfitting Reference Baseline**: Retraining and evaluating on the same split yields an overfitted artifact ($P@1 = 1.0000$), which is documented as a negative control reference point.

### 2.2 Multi-Fold Cross Validation (ILDC 1,500 Query Corpus)
- 5-Fold cross-validation across 1,500 authentic Supreme Court of India query-judgment pairs.
- Evaluates authorized Precision@1, Recall@K, and Mean Reciprocal Rank (MRR).

---

## 3. Quantitative Evaluation Metrics

- **Precision@1 ($P@1$)**: Percentage of top-ranked legal citations that exactly match authoritative precedent.
- **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant precedent across $N$ queries:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- **Zero-Trust Isolation Leakage**: Percentage of unauthorized document chunks leaking across tenant access boundaries.
- **Groth16 Proving Latency**: Mean wall-clock time (ms) to compute 192-byte Groth16 witness and proof.
- **Fabric Consensus Throughput**: Transactions per second (TPS) processed by 4-node Raft consensus cluster under concurrent load.

---

## 4. Baseline Comparison Conditions

1. **Condition 1 (Naive Dense RAG)**: Dense vector search without ABAC isolation or re-ranking.
2. **Condition 2 (ABAC + Naive Dense RAG)**: Zero-trust ABAC policy filter applied before vector search.
3. **Condition 3 (VADP Full Pipeline: ABAC + GBT Re-ranker)**: Zero-trust ABAC policy filter + GBT re-ranker + NLI entailment gate.
