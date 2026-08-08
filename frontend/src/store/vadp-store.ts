import { create } from "zustand";
import type {
  VerificationContract,
  ContractVerificationResult,
  ContractEvent,
} from "@/types/vadp";

interface VADPState {
  contracts: VerificationContract[];
  selectedContract: VerificationContract | null;
  verificationResult: ContractVerificationResult | null;
  timelineEvents: ContractEvent[];
  isLoading: boolean;
  error: string | null;

  setContracts: (contracts: VerificationContract[]) => void;
  setSelectedContract: (contract: VerificationContract | null) => void;
  setVerificationResult: (result: ContractVerificationResult | null) => void;
  setTimelineEvents: (events: ContractEvent[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useVADPStore = create<VADPState>((set) => ({
  contracts: [],
  selectedContract: null,
  verificationResult: null,
  timelineEvents: [],
  isLoading: false,
  error: null,

  setContracts: (contracts) => set({ contracts }),
  setSelectedContract: (contract) => set({ selectedContract: contract }),
  setVerificationResult: (verificationResult) => set({ verificationResult }),
  setTimelineEvents: (timelineEvents) => set({ timelineEvents }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      contracts: [],
      selectedContract: null,
      verificationResult: null,
      timelineEvents: [],
      isLoading: false,
      error: null,
    }),
}));
