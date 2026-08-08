# VADP — Verifiable AI Decision Provenance for AI-Assisted Judicial Decision Support

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](requirements/requirements.txt)
[![Coverage: 96.4%](https://img.shields.io/badge/coverage-96.4%25-brightgreen.svg)](results/raw/coverage.xml)
[![Tests: 115 Passed](https://img.shields.io/badge/tests-115%20passed-success.svg)](backend/tests/)

Official software implementation and empirical verification repository for **VADP (Verifiable AI Decision Provenance)**.

---

## 1. Research & System Objective

Modern AI decision support systems deployed in judicial workflows face severe trustworthiness challenges, including hallucinated legal precedents, unverified prompt context leakage, and post-hoc manipulation of AI-generated advice. 

**VADP (Verifiable AI Decision Provenance)** resolves these challenges by introducing a zero-trust, end-to-end verifiable decision support architecture that combines:
1. **Zero-Trust ABAC Policy Enforcement**: Guarantees strict context isolation across judicial clearance boundaries ($0.00\%$ context leakage).
2. **RFC 6962 Merkle Audit Ledger**: Seals decision inputs, retrieval citations, and prompt hashes in a tamper-evident cryptographic hash chain.
3. **Groth16 Zero-Knowledge Proofs**: Generates sub-second BN128 ZK-SNARK inclusion proofs ($192\text{ bytes}$) to verify private document inclusion without disclosing confidential case text.
4. **Gradient Boosted Legal Re-Ranker**: Recovers high precedent retrieval accuracy ($P@1 = 94.2\%$, $\text{MRR} = 0.951$) while mitigating out-of-distribution overfitting.
5. **Standardized Verification Contracts**: Exports self-contained, machine-verifiable integrity contracts per SCITT transparency profiles.

---

## 2. Repository Architecture & Directory Hierarchy

```
VADP/
├── README.md                            # Primary Software Guide
├── LICENSE                              # MIT License
├── CITATION.cff                         # Citation Metadata File
├── CHANGELOG.md                         # Release Changelog
├── .gitignore                           # Research Git Exclusion Rules
├── docker-compose.yml                   # Container Orchestration Config
│
├── src/                                 # Canonical Modular Source Implementation
│   ├── authorization/                   # Zero-Trust ABAC PDP Policy Engine
│   ├── provenance/                      # Merkle Tree Audit Ledger & Hash Chains
│   ├── verification/                    # Verification Contract Generator & Validator
│   ├── evidence/                        # Groth16 ZKP Prover, PKCS#11 Vault & Fabric Anchor
│   ├── rag/                             # Hybrid Retrieval, GBT Re-Ranker & NLI Gate
│   ├── core/                            # Configuration, Logging, Exceptions & DB
│   └── llm/                             # LLM Client & Prompt Injection Guardrails
│
├── experiments/                         # Scientific Evaluation & Benchmark Harnesses
│   ├── reproduce_results.py             # Single-Command Result Verification Harness
│   ├── baselines/                       # Naive Dense RAG & LexGLUE Baselines
│   ├── retrieval/                       # Disjoint Held-Out Retraining Scripts
│   ├── security/                        # STRIDE / MITRE ATLAS Penetration Suite
│   ├── zk_crypto/                       # Groth16 MPC Ceremony & SoftHSM Benchmarks
│   └── blockchain/                      # Multi-Node Fabric Consensus TPS Benchmarks
│
├── tests/                               # Automated Test Infrastructure (115 Tests)
│   ├── unit/                            # Unit Test Suite Across 18 Tiers (70 Tests)
│   ├── integration/                     # End-to-End Pipeline Verification
│   └── security/                        # Dedicated Penetration Tests (31 Tests)
│
├── data/                                # Dataset Manifests & Acquisition Documentation
│   ├── README.md                        # Dataset Access, Licenses & Split Schemas
│   └── manifests/                       # Precomputed Schemas & Disjoint Splits
│
├── results/                             # Empirical Evaluation Outputs
│   ├── tables/                          # Formatted Benchmark Results (Tables 1-8)
│   ├── figures/                         # High-Res Confusion Matrix & Calibration Plots
│   └── raw/                             # Micro-benchmark Traces & Coverage Logs
│
├── docs/                                # Technical & Methodological Documentation
│   ├── ARCHITECTURE.md                  # Deep System Architecture Specifications
│   ├── METHODOLOGY.md                   # Evaluation Protocols & Disjoint Split Design
│   └── REPRODUCIBILITY.md               # Step-by-Step Reproduction Guide
│
├── keys/                                # Isolated Demonstration Certificates
│   └── demo_only/                       # Mock KMS & SoftHSM Test PEM Keys
│
└── requirements/                        # Pinned Dependency Environments
    ├── requirements.txt                 # Python Pinned Requirements (3.10+)
    └── environment.yml                  # Conda Environment Definition
```

---

## 3. Quick Start & Installation

### Prerequisites
- Python 3.10 or higher (Python 3.12 recommended)
- Git

```bash
# 1. Clone the repository
git clone https://github.com/vadp-research/vadp.git
cd vadp

# 2. Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements/requirements.txt
```

---

## 4. Running Benchmark Results Verification

To verify all empirical benchmark results (Security Controls, Groth16 ZKP Latency, Fabric Blockchain Throughput, LexGLUE Retrieval, and System Coverage), run:

```bash
python experiments/reproduce_results.py
```

### Empirical Results Verification Matrix

| Component | Target System Claim | Key Metric | Verification Script | Output Result Log |
| :--- | :--- | :--- | :--- | :--- |
| **ABAC PDP Engine** | Zero-Trust Context Isolation | $0.00\%$ Leakage | `python -m pytest backend/tests/security` | `results/tables/ADVERSARIAL_NEGATIVE_TESTS.json` |
| **Groth16 ZKP Vault** | ZKP Proof Gen & Verification | $250.60\text{ ms}$ (warm), $11.31\text{ ms}$ verifier | `python experiments/reproduce_results.py` | `results/tables/GROTH16_MPC_TRUSTED_SETUP_COST.json` |
| **SoftHSM Token Vault** | PKCS#11 Hardware Token Signing | $1,000\text{ ops}$ verified | `python experiments/reproduce_results.py` | `results/tables/HSM_SIGNING_BENCHMARK.json` |
| **GBT Legal Re-Ranker** | Precedent Retrieval | $P@1 = 94.2\%$, $\text{MRR} = 0.951$ | `python experiments/reproduce_results.py` | `results/tables/BASELINES_COMPARISON_BENCHMARK.json` |
| **LexGLUE Disjoint** | Held-Out Retraining | $P@1 = 0.684$, $\text{MRR} = 0.762$ | `python experiments/reproduce_results.py` | `results/tables/LEXGLUE_DISJOINT_BENCHMARK.json` |
| **STRIDE Security Suite** | Penetration Controls | $26/26$ Passed | `python -m pytest backend/tests/security` | `results/tables/ADVERSARIAL_NEGATIVE_TESTS.json` |
| **Automated Test Scale** | System Test Infrastructure | $115$ Tests ($96.4\%$ Branch Cov) | `python -m pytest backend/tests` | `results/raw/coverage.xml` |
| **Fabric Blockchain** | 4-Node Consensus Anchoring | $24.27\text{ TPS}$, $41.26\text{ ms}$ P50 | `python experiments/reproduce_results.py` | `results/tables/FABRIC_MULTINODE_BENCHMARK.json` |

---

## 5. Automated Test Suite

Execute the 115-test suite across unit, integration, and security tiers:

```bash
python -m pytest backend/tests -v
```

---

## 6. Security & Data Governance

### Security Model
- **Zero Production Secrets**: All API keys and environment secrets are configured strictly via `.env` files (excluded from Git).
- **Isolated Demonstration Keys**: Mock signing certificates located under `keys/demo_only/` are explicitly headers-marked as non-production mock artifacts.

### Dataset Privacy & Redistribution
Per legal copyright and license restrictions for judicial records, raw case text files are **not redistributed** directly in this repository. Complete acquisition scripts and HuggingFace manifest hashes are provided in [`data/README.md`](data/README.md).

---

## 7. Citation & License

### Citation
```bibtex
@article{vadp2026judicial,
  title={VADP: Verifiable AI Decision Provenance for AI-Assisted Judicial Decision Support},
  author={Mandloi, Aditya},
  email={adityamandloi10@gmail.com},
  year={2026}
}
```

### License
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
