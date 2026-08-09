# VADP Adversarial Fuzzing Suite Report

**Total Contracts Tested**: 10,000  
**Random Seed**: `42`  
**Tamper Detection Rate (TDR)**: **100.0000%** ✅  
**Mean Localization Latency**: **0.0861ms**  
**P95 Localization Latency**: 0.1514ms  

## Per-Perturbation-Type Results

| Perturbation Type | N Contracts | Detected | TDR (%) | Mean Latency (ms) |
| --- | --- | --- | --- | --- |
| `hash_flip` | 2,500 | 2,500 | **100.00%** ✅ | 0.0840ms |
| `abac_role_swap` | 2,500 | 2,500 | **100.00%** ✅ | 0.0841ms |
| `citation_id_swap` | 2,500 | 2,500 | **100.00%** ✅ | 0.0894ms |
| `timestamp_tamper` | 2,500 | 2,500 | **100.00%** ✅ | 0.0870ms |

## Perturbation Descriptions

| # | Type | Attack Vector | Detection Method |
| --- | --- | --- | --- |
| 1 | `hash_flip` | 1-bit XOR flip in contract_hash hex string | Hash recomputation mismatch |
| 2 | `abac_role_swap` | Replace `judge` → `unauthorized_guest` in allowed_roles | Canonical JSON hash mismatch |
| 3 | `citation_id_swap` | Swap valid chunk_id with random UUID in rag_citations | Canonical JSON hash mismatch |
| 4 | `timestamp_tamper` | ±86,400 second shift of bsa_seal_timestamp | Canonical JSON hash mismatch |

## Conclusion

> **TDR = 100.0000%** — All 10,000 adversarial perturbations were correctly detected by the VADP cryptographic verification layer. Zero false negatives.