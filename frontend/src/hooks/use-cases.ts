/**
 * Nyaya-ZTA — Cases Custom Hook
 *
 * Provides operations to list cases, file a new case, and fetch case details.
 */

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useCaseStore } from "@/store/case-store";
import type { Case, CaseCreateRequest, CaseListResponse } from "@/types/case";

export function useCases() {
  const { cases, selectedCase, totalCases, setCases, setSelectedCase, addCase } = useCaseStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(
    async (params?: { status?: string; case_type?: string; page?: number }) => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiClient.get<CaseListResponse>("/cases", params);
        setCases(data.items, data.total);
      } catch (err: any) {
        setError(err.message || "Failed to fetch cases.");
      } finally {
        setIsLoading(false);
      }
    },
    [setCases]
  );

  const fetchCaseById = useCallback(
    async (id: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiClient.get<Case>(`/cases/${id}`);
        setSelectedCase(data);
        return data;
      } catch (err: any) {
        setError(err.message || "Failed to fetch case details.");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [setSelectedCase]
  );

  const fileCase = async (payload: CaseCreateRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<Case>("/cases", payload);
      addCase(data);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to file case.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    cases,
    selectedCase,
    totalCases,
    isLoading,
    error,
    fetchCases,
    fetchCaseById,
    fileCase,
  };
}
