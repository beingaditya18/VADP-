/**
 * VADP — AI Zustand Store
 *
 * Client-side state management for active AI analysis, SHAP values, trust scores, and recommendations.
 */

import { create } from "zustand";
import type { AIRecommendation, CaseAnalysisResponse } from "@/types/ai";

export type { CaseAnalysisResponse };

interface AIState {
  currentAnalysis: CaseAnalysisResponse | null;
  recommendations: AIRecommendation[];
  isLoading: boolean;

  setCurrentAnalysis: (analysis: CaseAnalysisResponse | null) => void;
  setRecommendations: (recs: AIRecommendation[]) => void;
  setIsLoading: (loading: boolean) => void;
}

export const useAIStore = create<AIState>((set) => ({
  currentAnalysis: null,
  recommendations: [],
  isLoading: false,

  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  setRecommendations: (recs) => set({ recommendations: recs }),
  setIsLoading: (isLoading) => set({ isLoading }),
}));
