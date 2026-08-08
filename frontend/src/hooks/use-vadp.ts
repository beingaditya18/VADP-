import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import type {
  VerificationContract,
  ContractVerificationResult,
  ContractEvent,
} from "@/types/vadp";

export function useVADP() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getContract = useCallback(async (contractId: string): Promise<VerificationContract | null> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<VerificationContract>(`/vadp/contracts/${contractId}`);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to fetch Verification Contract");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getContractByRecommendation = useCallback(async (recId: string): Promise<VerificationContract | null> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<VerificationContract>(`/vadp/recommendations/${recId}/contract`);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to fetch contract for recommendation");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getContractsForCase = useCallback(async (caseId: string): Promise<VerificationContract[]> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<VerificationContract[]>(`/vadp/cases/${caseId}/contracts`);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to fetch contracts for case");
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyContract = useCallback(async (contractId: string): Promise<ContractVerificationResult | null> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<ContractVerificationResult>(`/vadp/contracts/${contractId}/verify`);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to execute independent verification");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reviewContract = useCallback(async (contractId: string, action: string, notes?: string): Promise<VerificationContract | null> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<VerificationContract>(`/vadp/contracts/${contractId}/review`, {
        action,
        notes,
      });
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to record contract review");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const finalizeContract = useCallback(async (contractId: string): Promise<VerificationContract | null> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<VerificationContract>(`/vadp/contracts/${contractId}/finalize`);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to finalize contract");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getTimeline = useCallback(async (contractId: string): Promise<ContractEvent[]> => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<ContractEvent[]>(`/vadp/contracts/${contractId}/timeline`);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to fetch provenance timeline");
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    getContract,
    getContractByRecommendation,
    getContractsForCase,
    verifyContract,
    reviewContract,
    finalizeContract,
    getTimeline,
  };
}
