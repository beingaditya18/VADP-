# Multi-Tenant Latency Benchmark (Issue #9)

**N per tenant**: 100 | **Duration/trial**: 2.0s | **Trials**: 2
**T1**: district_court_indore | **T2**: district_court_bhopal

## Pattern Results

| Pattern | T1 QPS | T2 QPS | Combined QPS | T1 P99 (ms) | T2 P99 (ms) |
| --- | --- | --- | --- | --- | --- |
| P1: Both Read-Only | 28197.0 ± 682.5 | 28253.2 ± 786.8 | 56450.2 | 0.1 | 0.1 |
| P2: T1 Read / T2 Write | 111435.2 ± 12.2 | (write: 5.0) | 111435.2 | 0.0 | — |
| P3: T1+T2 Concurrent Read | 29393.5 ± 555.0 | 29058.8 ± 469.2 | 58452.3 | 0.1 | 0.1 |
| P4: T1+T2 Read + Write | 110020.2 ± 1539.2 | (write: 5.0) | — | 0.0 | — |

> **Tenant isolation**: T1 and T2 FAISS indices share no vectors.
> **Bottleneck**: Write contention under concurrent read+write.
> SQLite WAL serialization is the primary write-path bottleneck.