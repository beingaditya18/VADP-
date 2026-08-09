# VADP System Cryptographic Performance Benchmark Report

**Generated At**: `2026-07-25 09:17:14 UTC`  
**Evaluated Sample**: `100 Verification Contracts`  
**Signing Algorithm**: `ECDSA-P256-SHA256 (NIST P-256)`  
**Merkle Tree Leaf Format**: `RFC 6962 SHA-256`  

---

## 1. Latency Metrics Summary (100 Contracts)

| Cryptographic Operation | P50 (Median) | P95 | P99 | Mean Latency | Throughput (ops/sec) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Contract SHA-256 Hashing** | `0.0483 ms` | `0.061 ms` | `0.097 ms` | `0.0516 ms` | `19,379.84 ops/s` |
| **ECDSA P-256 Signature Verification** | `0.0161 ms` | `0.0207 ms` | `0.0911 ms` | `0.0766 ms` | `13,054.83 ops/s` |
| **Merkle Leaf & Proof Verification** | `0.0025 ms` | `0.0033 ms` | `0.004 ms` | `0.0028 ms` | `357,142.86 ops/s` |
| **Completeness Invariant Evaluation** | `0.0095 ms` | `0.0135 ms` | `0.0216 ms` | `0.0102 ms` | `98,039.22 ops/s` |
| **Full Independent Contract Verification** | `2.0863 ms` | `2.6428 ms` | `2.8203 ms` | `2.1704 ms` | **`460.74 v/sec`** |

---

## 2. Key Takeaways & Claims Verification

1. **Sub-Millisecond Merkle Verification**: Merkle leaf and inclusion proof verification runs at **`0.0025 ms`** (P50), satisfying sub-millisecond requirements.
2. **ECDSA Signature Performance**: NIST P-256 digital signature verification completes in **`0.0161 ms`** (P50).
3. **End-to-End Verification Throughput**: Full contract re-hashing, signature check, Merkle proof validation, and DB evidence cross-verification executes in **`2.0863 ms`** (P50) per contract (**`460.74 contracts/sec`**).

---

## 3. Benchmark Execution Command

To reproduce these benchmark numbers from scratch:

```powershell
python scripts/benchmark_vadp.py
```
