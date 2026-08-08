/**
 * VADP — Ledger Custom Hook
 *
 * Provides operations to fetch audit blocks, seal new blocks, and verify chain integrity.
 */

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useLedgerStore } from "@/store/ledger-store";
import type { LedgerBlock, ChainVerificationResult, MerkleProofResponse } from "@/types/ledger";

export function useLedger() {
  const { blocks, verificationResult, setBlocks, setVerificationResult } = useLedgerStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBlocks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<LedgerBlock[]>("/ledger/blocks");
      setBlocks(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch ledger blocks.");
    } finally {
      setIsLoading(false);
    }
  }, [setBlocks]);

  const verifyChain = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiClient.get<ChainVerificationResult>("/ledger/verify");
      setVerificationResult(result);
      return result;
    } catch (err: any) {
      setError(err.message || "Failed to verify chain integrity.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [setVerificationResult]);

  const sealBlock = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const newBlock = await apiClient.post<LedgerBlock | null>("/ledger/blocks/seal");
      await fetchBlocks();
      await verifyChain();
      return newBlock;
    } catch (err: any) {
      setError(err.message || "Failed to seal new block.");
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const getMerkleProof = async (entryId: string) => {
    try {
      return await apiClient.get<MerkleProofResponse>(`/ledger/entries/${entryId}/proof`);
    } catch {
      return null;
    }
  };

  return {
    blocks,
    verificationResult,
    isLoading,
    error,
    fetchBlocks,
    verifyChain,
    sealBlock,
    getMerkleProof,
  };
}
