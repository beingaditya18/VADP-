# Empirical Comparison: VADP vs. Sachan & Liu (2024)

**Corpus Size**: 1,500 Queries | **Evaluation Environment**: Local Single Machine

## 1. Batch Size Sweep (Sachan & Liu 2024) vs. VADP Per-Decision Contract

| Architecture | Batch Size (B) | Commit Latency / Decision (ms) | Audit Time / Decision (ms) | Storage Footprint (Bytes/Record) | Tamper Detection Granularity |
| --- | --- | --- | --- | --- | --- |
| Sachan & Liu (2024) | B=10 | 0.0012 ms | 0.0010 ms | 287.2 B | Delayed Batch Detection (Window = 10 decisions) |
| Sachan & Liu (2024) | B=50 | 0.0010 ms | 0.0010 ms | 284.64 B | Delayed Batch Detection (Window = 50 decisions) |
| Sachan & Liu (2024) | B=100 | 0.0010 ms | 0.0010 ms | 284.32 B | Delayed Batch Detection (Window = 100 decisions) |
| Sachan & Liu (2024) | B=500 | 0.0010 ms | 0.0010 ms | 284.06 B | Delayed Batch Detection (Window = 500 decisions) |
| **VADP (Ours)** | **Per-Decision (B=1)** | **1.5499 ms** | **0.0116 ms** | **866 B** | **Immediate Per-Decision (O(1) emission)** |

## 2. Tamper Localization Benchmark (1 Record Tampered in N=1,500)

| Strategy | Complexity | Localization Time (ms) | Records Scanned | Tamper Detected |
| --- | --- | --- | --- | --- |
| Sachan & Liu (B=500) | O(B) Batch Re-Scan | 0.0271 ms | 500 records | ✅ YES |
| **VADP RFC 6962** | **O(log K) Proof** | **0.0160 ms** | **1 record** | ✅ YES |