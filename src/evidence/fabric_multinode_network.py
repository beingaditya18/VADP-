"""
Multi-Node Hyperledger Fabric Network Deployment & Verification Manager
========================================================================

Simulates and evaluates multi-node Enterprise Hyperledger Fabric deployment for VADP Evidence Vault.
Topology:
  - 4 Organizations (HighCourtMSP, DistrictCourtMSP, ForensicLabMSP, SupremeCourtMSP)
  - 2 Peer Nodes per Organization (8 total peers)
  - 3-node Raft Ordering Service Cluster (orderer1, orderer2, orderer3)
  - Endorsement Policy: AND('HighCourtMSP.peer', 'ForensicLabMSP.peer', OR('DistrictCourtMSP.peer', 'SupremeCourtMSP.peer'))
  - Fabric Channels: `judiciary-evidence-channel`, `appeals-audit-channel`
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PeerNodeConfig(BaseModel):
    peer_id: str
    org_msp_id: str
    endpoint: str
    gRPC_port: int
    status: str = "ONLINE"
    latency_ms: float = 2.5


class EndorsementPolicy(BaseModel):
    policy_expr: str = "AND('HighCourtMSP.peer', 'ForensicLabMSP.peer', OR('DistrictCourtMSP.peer', 'SupremeCourtMSP.peer'))"
    required_endorsements: int = 3
    quorums_satisfied: bool = True


class MultiNodeAnchorBlock(BaseModel):
    block_number: int
    channel_id: str
    previous_hash: str
    data_hash: str
    tx_count: int
    endorsements: List[Dict[str, str]]
    timestamp_iso: str
    consensus_type: str = "Raft"
    leader_orderer: str = "orderer1.judicial.gov.in:7050"


class MultiNodeFabricNetwork:
    """
    Simulates a production multi-node Hyperledger Fabric deployment across multiple judicial institutions.
    """

    def __init__(self, channel_id: str = "judiciary-evidence-channel") -> None:
        self.channel_id = channel_id
        self.endorsement_policy = EndorsementPolicy()
        self.peers = self._setup_peers()
        self.blockchain_ledger: List[MultiNodeAnchorBlock] = []
        self._genesis_block()

    def _setup_peers(self) -> List[PeerNodeConfig]:
        orgs = ["HighCourtMSP", "DistrictCourtMSP", "ForensicLabMSP", "SupremeCourtMSP"]
        peers = []
        for org in orgs:
            for idx in range(2):
                peer_id = f"peer{idx}.{org.lower()}.judicial.gov.in"
                peers.append(
                    PeerNodeConfig(
                        peer_id=peer_id,
                        org_msp_id=org,
                        endpoint=f"{peer_id}:7051",
                        gRPC_port=7051 + len(peers),
                        latency_ms=round(random.uniform(1.2, 4.8), 2),
                    )
                )
        return peers

    def _genesis_block(self) -> None:
        genesis = MultiNodeAnchorBlock(
            block_number=0,
            channel_id=self.channel_id,
            previous_hash="0" * 64,
            data_hash=hashlib.sha256(b"VADP_MULTI_NODE_GENESIS").hexdigest(),
            tx_count=1,
            endorsements=[{"msp": "HighCourtMSP", "signature": "GENESIS_SIG"}],
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )
        self.blockchain_ledger.append(genesis)

    def submit_endorsed_transaction(
        self,
        evidence_id: str,
        case_id: str,
        content_hash: str,
        merkle_root: str,
        simulated_by: str = "Judicial Registrar",
    ) -> Dict[str, Any]:
        """
        Simulates proposal dispatch to peers, endorsement collection, Raft ordering, and block commit.
        """
        t0 = time.perf_counter()

        # Collect Endorsements from required orgs
        endorsing_orgs = ["HighCourtMSP", "ForensicLabMSP", "DistrictCourtMSP"]
        endorsements = []
        total_latency = 0.0

        for org in endorsing_orgs:
            target_peer = next(p for p in self.peers if p.org_msp_id == org and p.status == "ONLINE")
            total_latency += target_peer.latency_ms
            sig = hashlib.sha256(f"{target_peer.peer_id}:{content_hash}".encode()).hexdigest()[:32]
            endorsements.append({"peer": target_peer.peer_id, "msp": org, "signature": sig})

        # Calculate block commit
        prev_block = self.blockchain_ledger[-1]
        data_payload = json.dumps({
            "evidence_id": evidence_id,
            "case_id": case_id,
            "content_hash": content_hash,
            "merkle_root": merkle_root,
            "endorsements": endorsements,
        }, sort_keys=True).encode()

        data_hash = hashlib.sha256(data_payload).hexdigest()
        block_number = len(self.blockchain_ledger)

        new_block = MultiNodeAnchorBlock(
            block_number=block_number,
            channel_id=self.channel_id,
            previous_hash=prev_block.data_hash,
            data_hash=data_hash,
            tx_count=1,
            endorsements=endorsements,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )
        self.blockchain_ledger.append(new_block)

        elapsed_ms = round((time.perf_counter() - t0) * 1000 + total_latency, 2)

        return {
            "status": "SUCCESS",
            "block_number": block_number,
            "channel_id": self.channel_id,
            "tx_id": data_hash[:32],
            "endorsements_collected": len(endorsements),
            "endorsement_policy_satisfied": len(endorsements) >= self.endorsement_policy.required_endorsements,
            "network_latency_ms": elapsed_ms,
            "block_hash": data_hash,
        }

    def verify_network_integrity(self) -> Dict[str, Any]:
        """
        Validates hash chain continuity across multi-node block ledger.
        """
        for i in range(1, len(self.blockchain_ledger)):
            curr = self.blockchain_ledger[i]
            prev = self.blockchain_ledger[i - 1]
            if curr.previous_hash != prev.data_hash:
                return {"valid": False, "broken_at_block": i}
        return {
            "valid": True,
            "total_blocks": len(self.blockchain_ledger),
            "total_peers": len(self.peers),
            "active_orgs": 4,
            "consensus": "Raft (3 Orderers)",
        }
