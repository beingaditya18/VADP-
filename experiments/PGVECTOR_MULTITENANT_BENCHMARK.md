# PostgreSQL + pgvector Multi-Tenant Scale & Concurrency Report

**Scope Boundary**: Single-instance scaling and isolation were empirically validated (10 to 250 concurrent sessions); multi-node physical replication remains future work.

## Active Concurrency Benchmark Results

| Concurrent Sessions | Index Type | RLS Status | P50 (ms) | P95 (ms) | P99 (ms) | QPS (↑) | Tenant Leak Count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | pgvector HNSW | RLS Enabled | 2.57 ms | 3.62 ms | 4.41 ms | 3552.86 QPS | 0 (0.00%) |
| 50 | pgvector HNSW | RLS Enabled | 4.66 ms | 6.79 ms | 12.34 ms | 6349.23 QPS | 0 (0.00%) |
| 100 | pgvector HNSW | RLS Enabled | 7.06 ms | 10.62 ms | 14.07 ms | 4317.46 QPS | 0 (0.00%) |
| 250 | pgvector HNSW | RLS Enabled | 14.36 ms | 22.14 ms | 23.06 ms | 2179.70 QPS | 0 (0.00%) |