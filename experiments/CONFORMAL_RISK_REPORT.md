# Theorem 2 — Conformal Risk Threshold Empirical Validation

**Target miss-risk**: α = 0.05 (5%)  
**Calibration set**: N = 500 held-out cases (Y ∈ {0,1} appellate outcomes)  
**Validation set**: N = 200 held-out cases  

## Computed Conformal Threshold

| Parameter | Value |
| --- | --- |
| **τ̂_p** (conformal threshold) | `0.490814` |
| **Decision threshold** (1 - τ̂_p) | `0.509186` |
| **Non-conformity scores (N)** | 256 |
| **Non-conformity score mean** | 0.4163 |

## Bounded Error Validation on 200 Held-Out Cases

| Metric | Value | Target |
| --- | --- | --- |
| **Miss rate** | 4.5000% | ≤ 5% |
| **Missed cases** | 9 / 200 | — |
| **Bound satisfied** | **✅ YES** | TRUE |
| **Coverage rate** | 89.50% | — |

> **Theorem 2 ✅ EMPIRICALLY SATISFIED**: The conformal threshold τ̂_p = 0.490814 achieves a miss-rate of 4.5000% ≤ 5% on the 200-case validation set.