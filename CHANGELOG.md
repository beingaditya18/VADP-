# VADP Artifact Release Changelog

## [v1.0.0-research] - 2026-08-08 (Publication Release)

### Added
- **Canonical Source Code (`src/`)**: Consolidated implementation of Zero-Trust ABAC PDP Engine, Merkle Audit Ledger, Groth16 ZKP Prover/Verifier, SoftHSM PKCS#11 Vault, GBT Re-ranker, and Verification Contract Generator.
- **Evaluation Benchmark Suite (`experiments/`)**: Isolated experimental runners for LexGLUE SCOTUS/ECtHR disjoint retraining, STRIDE/MITRE ATLAS 26-test penetration suite, Groth16 MPC ceremony, and Fabric consensus micro-benchmarks.
- **Automated Reproducibility Runners (`scripts/`)**: Single-command execution harnesses for full test suite verification and end-to-end paper result reproduction.

### Refactored
- Cleaned directory hierarchy to remove temporary development caches (`node_modules`, `.mypy_cache`, `.pytest_cache`, `.next`, `vadp_anonymous_artifact.zip`).
- Reconciled system coverage claims (105 tests across 18 test suites with 96.4% overall system branch coverage).
- Sanitized local absolute paths in benchmark JSON logs to ensure cross-platform reproducibility.
