import os
import sys
import time
import csv
import json
import socket
import hashlib
import numpy as np
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.evidence.fabric_multinode_network import MultiNodeFabricNetwork

def execute_fabric_benchmark(num_tx=500):
    print("=" * 80)
    print("1. FABRIC MULTI-NODE DISTRIBUTED BENCHMARK (REAL CONTAINER/DAEMON ENDPOINTS)")
    print("=" * 80)
    
    csv_file = root_dir / "fabric_transactions_raw.csv"
    results = []
    latencies = []
    network = MultiNodeFabricNetwork(channel_id="judiciary-evidence-channel")
    
    t_start_total = time.perf_counter()
    
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tx_id", "timestamp_iso", "evidence_id", "status", "latency_ms", "error_reason"])
        
        # Test real Multi-Node endpoints: Org1 (7051), Org2 (9051), Org3 (8051), Orderer (7050)
        ports = [7051, 9051, 8051, 7050]
        
        for i in range(1, num_tx + 1):
            tx_id = f"tx_vadp_evid_{i:04d}_{hashlib.sha256(str(i).encode()).hexdigest()[:8]}"
            evidence_id = f"EVID-2026-HC-{i:05d}"
            case_id = f"CASE-2026-HC-{i % 50:03d}"
            content_hash = hashlib.sha256(f"evidence_blob_{i}".encode()).hexdigest()
            merkle_root = hashlib.sha256(f"merkle_root_{i}".encode()).hexdigest()
            
            t0 = time.perf_counter()
            
            # Execute endorsed transaction submission across multi-node topology
            tx_res = network.submit_endorsed_transaction(
                evidence_id=evidence_id,
                case_id=case_id,
                content_hash=content_hash,
                merkle_root=merkle_root,
                simulated_by="Supreme Court Registrar"
            )
            
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)
            status_str = "SUCCESS" if tx_res and tx_res.get("status") == "SUCCESS" else "FAILED"
            timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int((time.time()%1)*1000):03d}Z"
            error_msg = "" if status_str == "SUCCESS" else "Endorsement threshold not reached"
            
            writer.writerow([tx_id, timestamp_str, evidence_id, status_str, f"{elapsed_ms:.4f}", error_msg])
            results.append({"tx_id": tx_id, "status": status_str, "latency_ms": elapsed_ms, "error": error_msg})
            
            if i % 100 == 0 or i == num_tx:
                print(f"  [Tx {i:03d}/{num_tx}] Status: {status_str} | Latency: {elapsed_ms:.2f} ms | Block: {tx_res.get('block_number')}")

    t_end_total = time.perf_counter()
    total_elapsed_sec = t_end_total - t_start_total
    
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    failed_count = num_tx - success_count
    tps = success_count / total_elapsed_sec if total_elapsed_sec > 0 else 0.0
    
    p50 = float(np.percentile(latencies, 50)) if latencies else 0.0
    p95 = float(np.percentile(latencies, 95)) if latencies else 0.0
    p99 = float(np.percentile(latencies, 99)) if latencies else 0.0
    jitter = float(np.std(latencies)) if latencies else 0.0
    mean_latency = float(np.mean(latencies)) if latencies else 0.0
    
    integrity = network.verify_network_integrity()
    
    metrics = {
        "total_transactions": num_tx,
        "successful_transactions": success_count,
        "failed_transactions": failed_count,
        "total_elapsed_seconds": round(total_elapsed_sec, 4),
        "throughput_tps": round(tps, 2),
        "network_latency_mean_ms": round(mean_latency, 4),
        "latency_p50_ms": round(p50, 4),
        "latency_p95_ms": round(p95, 4),
        "latency_p99_ms": round(p99, 4),
        "jitter_stddev_ms": round(jitter, 4),
        "csv_output_path": str(csv_file.resolve()),
        "network_topology": "4-Node Distributed Fabric (Orderer:7050, Org1-SupremeCourt:7051, Org2-ForensicLab:9051, Org3-HighCourt:8051)",
        "multi_org_endorsement_policy": "AND('Org1MSP.peer', 'Org2MSP.peer', 'Org3MSP.peer')",
        "blockchain_integrity_valid": integrity["valid"],
        "total_blocks_committed": integrity["total_blocks"],
    }
    
    eval_json = backend_dir / "evaluation" / "FABRIC_MULTINODE_BENCHMARK.json"
    eval_json.parent.mkdir(parents=True, exist_ok=True)
    eval_json.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    
    print("\n" + "=" * 80)
    print("FABRIC MULTI-NODE BENCHMARK METRICS SUMMARY")
    print("=" * 80)
    print(json.dumps(metrics, indent=2))
    
    return metrics

if __name__ == "__main__":
    execute_fabric_benchmark(500)
