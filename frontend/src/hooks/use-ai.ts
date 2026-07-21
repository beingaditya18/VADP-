/**
 * Nyaya-ZTA — AI Custom Hook
 *
 * Operations to trigger case AI analysis, list recommendations, and submit Judge reviews.
 */

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useAIStore, type CaseAnalysisResponse } from "@/store/ai-store";
import type { AIRecommendation } from "@/types/ai";

export function useAI() {
  const { currentAnalysis, recommendations, isLoading, setCurrentAnalysis, setRecommendations, setIsLoading } = useAIStore();
  const [error, setError] = useState<string | null>(null);

  const analyzeCase = useCallback(async (caseId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<CaseAnalysisResponse>(`/ai/cases/${caseId}/analyze`);
      setCurrentAnalysis(data);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to analyze case.");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [setCurrentAnalysis, setIsLoading]);

  const fetchRecommendations = useCallback(async (caseId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<AIRecommendation[]>(`/ai/cases/${caseId}/recommendations`);
      setRecommendations(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch recommendations.");
    } finally {
      setIsLoading(false);
    }
  }, [setRecommendations, setIsLoading]);

  const reviewRecommendation = async (recommendationId: string, action: "approved" | "rejected" | "flagged") => {
    setIsLoading(true);
    setError(null);
    try {
      const updated = await apiClient.post<AIRecommendation>(
        `/ai/recommendations/${recommendationId}/review?action=${action}`
      );
      if (currentAnalysis && currentAnalysis.recommendation.id === recommendationId) {
        setCurrentAnalysis({
          ...currentAnalysis,
          recommendation: { ...currentAnalysis.recommendation, status: action },
        });
      }
      return updated;
    } catch (err: any) {
      setError(err.message || "Failed to submit recommendation review.");
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    currentAnalysis,
    recommendations,
    isLoading,
    error,
    analyzeCase,
    fetchRecommendations,
    reviewRecommendation,
  };
}
