# Human Override Coverage (HOC) Empirical Benchmark Report

**Generated At**: `2026-07-29 13:48:12 UTC`  
**Evaluation Scope**: `N = 378 Real ILDC Supreme Court Cases`  
**Escalation Algorithm**: `Algorithm 5 (Threshold Predicate: Trust < 0.88 OR Risk > 0.12)`  
**Empirical Result**: **`HOC = 68.25%`** (95% Wilson CI: `[63.4%, 72.74%]`)

---

## 1. Domain Category Breakdown (N = 378)

| Legal Domain Category | Total Cases | Escalated (HOC) | Auto-Approved | Category HOC (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Administrative** | `21` | `12` | `9` | `57.14%` |
| **Civil** | `4` | `4` | `0` | `100.00%` |
| **Commercial** | `14` | `6` | `8` | `42.86%` |
| **Constitutional** | `100` | `69` | `31` | `69.00%` |
| **Consumer** | `18` | `15` | `3` | `83.33%` |
| **Criminal** | `128` | `86` | `42` | `67.19%` |
| **Environmental** | `9` | `6` | `3` | `66.67%` |
| **Family Law** | `4` | `2` | `2` | `50.00%` |
| **Intellectual Property** | `6` | `5` | `1` | `83.33%` |
| **Labour** | `21` | `14` | `7` | `66.67%` |
| **Property** | `18` | `13` | `5` | `72.22%` |
| **Taxation** | `29` | `20` | `9` | `68.97%` |
| **civil** | `6` | `6` | `0` | `100.00%` |

---

## 2. Benchmark Execution Command

To reproduce this HOC empirical metric from scratch:

```powershell
python backend/scripts/evaluate_hoc.py
```
