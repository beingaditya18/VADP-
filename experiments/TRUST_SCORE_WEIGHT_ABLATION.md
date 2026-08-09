# VADP Trust Score Weight Ablation & Calibration Report

**Train Split**: N=1200 | **Held-out Test Split**: N=291
**Safety Guardrail**: $\alpha + \delta < 0.88$ (Prevents ungrounded model confidence)

## Performance Comparison

| Strategy | Weight Tuple (α, β, γ, δ) | ECE (↓) | Pearson r (↑) | Safety Guardrail |
| --- | --- | --- | --- | --- |
| **VADP Default** | `(0.35, 0.35, 0.15, 0.15)` | **0.130458** | **0.9835** | ✅ PASSED |
| **Grid Optimal** | `(0.0, 0.0, 1.0, 0.0)` | **0.098150** | **0.9720** | ✅ PASSED |
| **Learned Logistic** | `(0.0, 0.2089, 0.7911, 0.0)` | **0.101385** | **0.9794** | ✅ PASSED |

## Top 10 Candidate Weight Configurations (Ranked by ECE)

| Rank | α (Model) | β (Evidence) | γ (Source) | δ (Consistency) | ECE (↓) | Pearson r (↑) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.098150 | 0.9720 |
| 2 | 0.00 | 0.05 | 0.95 | 0.00 | 0.098924 | 0.9742 |
| 3 | 0.00 | 0.10 | 0.90 | 0.00 | 0.099699 | 0.9761 |
| 4 | 0.00 | 0.15 | 0.85 | 0.00 | 0.100473 | 0.9778 |
| 5 | 0.05 | 0.00 | 0.95 | 0.00 | 0.100657 | 0.9743 |
| 6 | 0.00 | 0.20 | 0.80 | 0.00 | 0.101248 | 0.9792 |
| 7 | 0.00 | 0.00 | 0.95 | 0.05 | 0.101263 | 0.9734 |
| 8 | 0.05 | 0.05 | 0.90 | -0.00 | 0.101431 | 0.9764 |
| 9 | 0.00 | 0.25 | 0.75 | 0.00 | 0.102022 | 0.9804 |
| 10 | 0.00 | 0.05 | 0.90 | 0.05 | 0.102038 | 0.9756 |