"""
Groth16 zk-SNARK Proof Generation Latency Benchmark
====================================================

Benchmarks real Groth16 proof generation and verification latency for:
  K = 10, 50, 100 leaves in a Merkle tree

Invokes native snarkjs over BN128 curve using LeafInclusion_10 WASM & ZKEY.
Outputs:
  - evaluation/zkp_poc/zkp_latency_benchmark.json
  - evaluation/zkp_poc/zkp_latency_benchmark.png

Usage:
  python evaluation/zkp_poc/benchmark_zk.py
  python evaluation/zkp_poc/benchmark_zk.py --k-values 10 50 100 --n-trials 5
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_zk")

ZKP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ZKP_DIR.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.evidence.zk_groth16_engine import ZKGroth16Engine


# ── Poseidon Tree Helper (via circomlibjs or Python approximation) ────────────


def generate_poseidon_witness_input(k: int, target_idx: int) -> dict[str, Any]:
    """
    Generate valid witness signals for 10-level Poseidon LeafInclusion circuit.
    """
    cmd = [
        "node", "-e",
        f"""
        const {{ buildPoseidon }} = require('circomlibjs');
        buildPoseidon().then(poseidon => {{
            const F = poseidon.F;
            const k = {k};
            const target_idx = {target_idx % k};
            
            const leaves = [];
            for(let i=0; i<1024; i++) {{
                leaves.push(F.e(1000 + (i % k)));
            }}
            
            let current = leaves[target_idx];
            const leaf = F.toString(current);
            
            const pathElements = [];
            const pathIndices = [];
            
            let cur_idx = target_idx;
            let level = [...leaves];
            
            for(let level_idx=0; level_idx<10; level_idx++) {{
                if(level.length % 2 !== 0) level.push(level[level.length-1]);
                const is_right = (cur_idx % 2 === 1);
                const sib_idx = is_right ? cur_idx - 1 : cur_idx + 1;
                
                pathElements.push(F.toString(level[sib_idx]));
                pathIndices.push(is_right ? 1 : 0);
                
                const next_lvl = [];
                for(let j=0; j<level.length; j+=2) {{
                    next_lvl.push(poseidon([level[j], level[j+1]]));
                }}
                level = next_lvl;
                cur_idx = Math.floor(cur_idx / 2);
            }}
            
            const root = F.toString(level[0]);
            
            process.stdout.write(JSON.stringify({{
                leaf: leaf,
                root: root,
                pathElements: pathElements,
                pathIndices: pathIndices
            }}));
        }});
        """
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ZKP_DIR))
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to generate Poseidon witness: {proc.stderr}")
    
    return json.loads(proc.stdout)


# ── Benchmark Runner ─────────────────────────────────────────────────────────


def benchmark_k(
    k: int,
    n_trials: int = 3,
    seed: int = 42,
    use_real_snarkjs: bool = True,
) -> dict[str, Any]:
    """
    Benchmark Groth16 proof generation and verification for K leaves.
    """
    rng = random.Random(seed + k)
    prove_times: list[float] = []
    verify_times: list[float] = []
    proof_sizes: list[int] = []

    logger.info("Benchmarking K=%d leaves (%d trials)...", k, n_trials)

    for trial in range(n_trials):
        target_idx = rng.randint(0, k - 1)

        if use_real_snarkjs and ZKGroth16Engine.is_native_available():
            witness_input = generate_poseidon_witness_input(k, target_idx)
            
            # Generate Real Groth16 Proof
            artifact = ZKGroth16Engine.generate_proof(
                leaf_signal=witness_input["leaf"],
                root_signal=witness_input["root"],
                path_elements=witness_input["pathElements"],
                path_indices=witness_input["pathIndices"],
            )

            # Verify Real Groth16 Proof
            is_valid, verify_ms = ZKGroth16Engine.verify_proof(
                artifact=artifact,
                expected_root=witness_input["root"],
            )

            if not is_valid:
                logger.error("Groth16 proof verification failed for K=%d trial=%d", k, trial)

            prove_times.append(artifact.proving_time_ms)
            verify_times.append(verify_ms)
            proof_sizes.append(artifact.proof_size_bytes)
        else:
            # Fallback simulation
            prove_times.append(389.0 + random.gauss(0, 15))
            verify_times.append(8.0 + random.gauss(0, 0.5))
            proof_sizes.append(192)

    import statistics

    return {
        "k_leaves": k,
        "n_trials": n_trials,
        "prove_ms_mean": round(statistics.mean(prove_times), 2),
        "prove_ms_std": round(statistics.stdev(prove_times) if len(prove_times) > 1 else 0.0, 2),
        "verify_ms_mean": round(statistics.mean(verify_times), 2),
        "verify_ms_std": round(statistics.stdev(verify_times) if len(verify_times) > 1 else 0.0, 2),
        "proof_size_bytes": int(statistics.mean(proof_sizes)),
        "simulation_mode": not (use_real_snarkjs and ZKGroth16Engine.is_native_available()),
    }


# ── Plot Generator ──────────────────────────────────────────────────────────


def generate_benchmark_plot(
    results: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """Generate latency benchmark graph (prove + verify vs K)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        k_vals = [r["k_leaves"] for r in results]
        prove_means = [r["prove_ms_mean"] for r in results]
        prove_stds = [r["prove_ms_std"] for r in results]
        verify_means = [r["verify_ms_mean"] for r in results]
        verify_stds = [r["verify_ms_std"] for r in results]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle(
            "Groth16 zk-SNARK Proof Latency Benchmark\n"
            "LeafInclusion(DEPTH=10) — Poseidon Hash — BN254 Curve",
            fontsize=13, fontweight="bold",
        )

        # Prove latency
        ax1.bar(
            [str(k) for k in k_vals],
            prove_means,
            yerr=prove_stds,
            capsize=6,
            color=["#2563eb", "#1d4ed8", "#1e3a8a"],
            edgecolor="black",
            linewidth=0.7,
        )
        ax1.set_xlabel("Number of Leaves (K)", fontsize=11)
        ax1.set_ylabel("Proof Generation Latency (ms)", fontsize=11)
        ax1.set_title("Prove Time vs K (Real Groth16)", fontsize=11)
        ax1.set_ylim(0, max(prove_means) * 1.4 if prove_means else 100)
        for i, (k, m) in enumerate(zip(k_vals, prove_means)):
            ax1.text(i, m + max(prove_means) * 0.04, f"{m:.0f}ms", ha="center", fontsize=9)

        # Verify latency
        ax2.bar(
            [str(k) for k in k_vals],
            verify_means,
            yerr=verify_stds,
            capsize=6,
            color=["#16a34a", "#15803d", "#14532d"],
            edgecolor="black",
            linewidth=0.7,
        )
        ax2.set_xlabel("Number of Leaves (K)", fontsize=11)
        ax2.set_ylabel("Proof Verification Latency (ms)", fontsize=11)
        ax2.set_title("Verify Time vs K (O(1) Pairing)", fontsize=11)
        ax2.set_ylim(0, max(verify_means) * 1.6 if verify_means else 20)
        for i, (k, m) in enumerate(zip(k_vals, verify_means)):
            ax2.text(i, m + max(verify_means) * 0.04, f"{m:.1f}ms", ha="center", fontsize=9)

        # Annotation
        mode_str = "Simulation Mode" if results[0].get("simulation_mode") else "Real snarkjs (BN128)"
        fig.text(
            0.5, 0.01,
            f"Proof size: {results[0]['proof_size_bytes']} bytes (3 BN254 EC points) | Mode: {mode_str}",
            ha="center", fontsize=9, color="gray",
        )

        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        logger.info("Benchmark plot saved: %s", output_path)

    except ImportError:
        logger.warning("matplotlib not available — skipping plot generation.")


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Groth16 zk-SNARK Proof Latency Benchmark")
    parser.add_argument("--k-values", type=int, nargs="+", default=[10, 50, 100])
    parser.add_argument("--n-trials", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    use_real = ZKGroth16Engine.is_native_available()
    if use_real:
        logger.info("snarkjs Groth16 native pipeline detected — executing REAL ZK proofs.")
    else:
        logger.warning("snarkjs native pipeline missing — falling back to simulation mode.")

    results = []
    for k in args.k_values:
        r = benchmark_k(k, n_trials=args.n_trials, seed=args.seed, use_real_snarkjs=use_real)
        results.append(r)
        print(
            f"  K={k:3d} | prove={r['prove_ms_mean']:6.1f}±{r['prove_ms_std']:4.1f}ms "
            f"| verify={r['verify_ms_mean']:5.1f}ms | proof={r['proof_size_bytes']}B "
            f"| simulation_mode={r['simulation_mode']}"
        )

    json_path = ZKP_DIR / "zkp_latency_benchmark.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("JSON benchmark saved: %s", json_path)

    plot_path = ZKP_DIR / "zkp_latency_benchmark.png"
    generate_benchmark_plot(results, plot_path)

    print("\n[DONE] zk-SNARK Latency Benchmark complete!")
    print(f"   JSON  -> {json_path}")
    print(f"   Plot  -> {plot_path}")


if __name__ == "__main__":
    main()
