/**
 * Nyaya-ZTA — Audit Ledger Zustand Store
 *
 * Client-side state management for block chain records and chain verification status.
 */

import { create } from "zustand";
import type { LedgerBlock, ChainVerificationResult } from "@/types/ledger";

interface LedgerState {
  blocks: LedgerBlock[];
  verificationResult: ChainVerificationResult | null;
  isLoading: boolean;

  setBlocks: (blocks: LedgerBlock[]) => void;
  setVerificationResult: (result: ChainVerificationResult) => void;
  setIsLoading: (loading: boolean) => void;
}

export const useLedgerStore = create<LedgerState>((set) => ({
  blocks: [],
  verificationResult: null,
  isLoading: false,

  setBlocks: (blocks) => set({ blocks }),
  setVerificationResult: (result) => set({ verificationResult: result }),
  setIsLoading: (isLoading) => set({ isLoading }),
}));
