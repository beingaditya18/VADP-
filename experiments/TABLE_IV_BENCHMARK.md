# Table IV — Multi-Baseline Judicial Retrieval Benchmark (N = 1,500 Queries)

| Condition | P@1 | P@3 | P@5 | P@10 | R@1 | R@3 | R@5 | R@10 | MRR | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Naive Dense RAG** | 0.719 | 0.293 | 0.184 | 0.097 | 0.144 | 0.176 | 0.184 | 0.194 | 0.801 | 13.1 |
| **BM25 Lexical** | 0.842 | 0.315 | 0.196 | 0.100 | 0.169 | 0.193 | 0.196 | 0.201 | 0.882 | 51.8 |
| **Cross-Encoder (`bge-reranker-base`)** | 0.889 | 0.338 | 0.206 | 0.103 | 0.178 | 0.201 | 0.206 | 0.210 | 0.918 | 2,621.3 |
| **VADP GBT Re-ranker (Ours)** | **0.931** | **0.352** | **0.214** | **0.107** | **0.187** | **0.209** | **0.214** | **0.217** | **0.951** | **16.3** |

## Condition Descriptions

| # | Condition | Implementation Details |
| --- | --- | --- |
| 1 | **Naive Dense RAG** | FAISS IndexFlatIP, cosine similarity, no re-ranking, no ZTA filtering |
| 2 | **BM25 Lexical** | Okapi BM25 (k1=1.5, b=0.75) over full chunk corpus |
| 3 | **Cross-Encoder** | BAAI/bge-reranker-base, dense top-50 candidate pool + CE re-ranking |
| 4 | **VADP GBT Re-ranker** | LambdaMART rank:pairwise + Sim(Q,Cj)×StatutoryMatch(Q,Cj) Semantic Precedent Relator |