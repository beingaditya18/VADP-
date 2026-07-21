/**
 * Nyaya-ZTA — Case Zustand Store
 *
 * Client-side state management for active case list and selected case details.
 */

import { create } from "zustand";
import type { Case } from "@/types/case";

interface CaseState {
  cases: Case[];
  selectedCase: Case | null;
  isLoading: boolean;
  totalCases: number;

  setCases: (cases: Case[], total: number) => void;
  setSelectedCase: (caseObj: Case | null) => void;
  addCase: (caseObj: Case) => void;
  setIsLoading: (loading: boolean) => void;
}

export const useCaseStore = create<CaseState>((set) => ({
  cases: [],
  selectedCase: null,
  isLoading: false,
  totalCases: 0,

  setCases: (cases, total) => set({ cases, totalCases: total }),
  setSelectedCase: (caseObj) => set({ selectedCase: caseObj }),
  addCase: (caseObj) => set((state) => ({ cases: [caseObj, ...state.cases], totalCases: state.totalCases + 1 })),
  setIsLoading: (isLoading) => set({ isLoading }),
}));
