# VADP Step-by-Step Software Reproducibility Guide

This guide provides step-by-step instructions to install, configure, verify, and reproduce all software system benchmarks, security tests, and empirical result tables.

---

## 1. System Requirements

- **Operating System**: Linux (Ubuntu 22.04 LTS recommended), macOS, or Windows 10/11.
- **Python**: Python 3.10+ (Python 3.12 recommended).
- **Node.js** (Optional, for Groth16 snarkjs compilation): Node v18+.
- **Hardware**: 8 GB RAM minimum, 4 CPU cores (No GPU required; CPU execution supported via FAISS-CPU).

---

## 2. Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/beingaditya18/VADP-.git
cd VADP-

# 2. Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install consolidated dependencies
pip install -r requirements/requirements.txt
```

---

## 3. Step 1: Automated Test Suite Execution (115 Tests)

Execute the complete 115-test suite across unit, integration, and security tiers:

```bash
# Run full pytest suite across all tiers
python -m pytest backend/tests -v
```

**Expected Result**:
- `115 passed`
- `Overall System Branch Coverage: 96.4%`

---

## 4. Step 2: System Benchmark & Results Verification

Run the single-command automated result verification harness:

```bash
python experiments/reproduce_results.py
```

This harness verifies and displays:
1. **Security Control Penetration Suite**: 26 dedicated security tests passing.
2. **Groth16 ZKP Proof Latency**: Proof generation ($250.60\text{ ms}$ warm) and verification ($11.31\text{ ms}$).
3. **Hyperledger Fabric Consensus**: 250 Fabric transaction micro-benchmarks ($24.27\text{ TPS}$).
4. **LexGLUE & ILDC GBT Re-ranking**: GBT re-ranker disjoint held-out evaluation ($P@1 = 0.684$, $\text{MRR} = 0.762$).
5. **Coverage & Test Scale**: System-wide $96.4\%$ branch coverage across 105 test suites.

---

## 5. Step 3: Security & Credentials Gate

To verify zero production secrets or hardcoded credentials across the codebase:

```bash
python -m pytest backend/tests/unit/test_secrets.py -v
```

**Expected Result**: `PASSED: ZERO HARDCODED SECRETS DETECTED`
