/**
 * VADP — Ledger Types
 *
 * Type definitions for the tamper-evident audit ledger.
 */

export interface LedgerBlock {
  id: string;
  block_index: number;
  timestamp: string;
  previous_hash: string;
  data_hash: string;
  merkle_root?: string;
  block_hash: string;
  signature?: string;
  nonce: number;
  entries_count: number;
  created_at: string;
  entries?: LedgerEntry[];
}

export interface LedgerEntry {
  id: string;
  block_id?: string;
  entry_type: string;
  actor_id?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  data_hash: string;
  entry_data: Record<string, unknown>;
  timestamp: string;
  created_at: string;
}

export interface MerkleProof {
  entry_id: string;
  entry_hash: string;
  proof_path: ProofNode[];
  merkle_root: string;
  is_valid: boolean;
}

export type MerkleProofResponse = MerkleProof;

export interface ProofNode {
  hash: string;
  position: "left" | "right";
}

export interface ChainVerificationResult {
  is_valid: boolean;
  total_blocks: number;
  verified_blocks: number;
  first_invalid_block?: number;
  verification_time_ms: number;
  details: string;
}
