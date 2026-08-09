# VADP Selective Prediction & Risk-Coverage Evaluation Report

## Theoretical Basis
This evaluation instantiates selective prediction under Chow's Rule (1970) and learning-to-defer theory (Mozannar & Sontag, 2020).
Rather than treating Human Override Coverage (HOC) as an ad-hoc threshold ratio, VADP formalizes the trade-off between automated coverage and empirical decision risk.

## Summary Metrics
- **Evaluated Recommendation Contracts**: 378
- **Target Risk Budget (epsilon)**: 5.0%
- **Optimal Trust Threshold (tau*)**: 0.7895
- **Achieved System Coverage**: 31.75%
- **Achieved Empirical Risk**: 5.83%
- **Accepted Decision Accuracy**: 94.17%
- **Area Under Risk-Coverage Curve (AURCC)**: 0.1114

## Empirical Risk-Coverage Trade-off Table

| Trust Threshold (tau) | Coverage (%) | Empirical Risk (%) | Accuracy (%) | Deferred Rate (%) |
|---|---|---|---|---|
| 0.00 | 100.0% | 27.8% | 72.2% | 0.0% |
| 0.11 | 100.0% | 27.8% | 72.2% | 0.0% |
| 0.21 | 100.0% | 27.8% | 72.2% | 0.0% |
| 0.32 | 99.5% | 27.4% | 72.6% | 0.5% |
| 0.42 | 95.2% | 24.2% | 75.8% | 4.8% |
| 0.53 | 87.8% | 20.5% | 79.5% | 12.2% |
| 0.63 | 72.0% | 14.3% | 85.7% | 28.0% |
| 0.74 | 47.9% | 7.7% | 92.3% | 52.1% |
| 0.84 | 21.2% | 6.2% | 93.8% | 78.8% |
| 0.95 | 4.0% | 6.7% | 93.3% | 96.0% |
