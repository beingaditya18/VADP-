/**
 * VADP — RAG Custom Hook
 *
 * Operations to send grounded RAG legal queries and index documents into FAISS vector store.
 */

import { useState } from "react";
import { apiClient } from "@/lib/api-client";
import { useRAGStore, type ChatMessage } from "@/store/rag-store";
import type { RAGQueryResponse } from "@/types/ai";

export function useRAG() {
  const { messages, isLoading, activeCaseId, addMessage, setIsLoading, setActiveCaseId, clearMessages } = useRAGStore();
  const [error, setError] = useState<string | null>(null);

  const askQuestion = async (queryText: string, caseId?: string) => {
    if (!queryText.trim()) return;

    setError(null);
    setIsLoading(true);

    const targetCaseId = caseId || activeCaseId || undefined;

    // Append user message
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      sender: "user",
      text: queryText,
      timestamp: new Date().toISOString(),
    };
    addMessage(userMsg);

    try {
      const response = await apiClient.post<RAGQueryResponse>("/rag/query", {
        query_text: queryText,
        case_id: targetCaseId,
      });

      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        sender: "ai",
        text: response.answer,
        citations: response.citations,
        processingTimeMs: response.processing_time_ms,
        timestamp: new Date().toISOString(),
      };
      addMessage(aiMsg);
      return response;
    } catch (err: any) {
      setError(err.message || "Failed to generate AI legal response.");
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        sender: "ai",
        text: `⚠️ Security/System Error: ${err.message || "Query failed."}`,
        timestamp: new Date().toISOString(),
      };
      addMessage(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const indexDocument = async (documentId: string) => {
    try {
      return await apiClient.post<{ chunks_indexed: number }>(`/rag/index/${documentId}`);
    } catch (err: any) {
      throw new Error(err.message || "Failed to index document.");
    }
  };

  return {
    messages,
    isLoading,
    error,
    activeCaseId,
    setActiveCaseId,
    askQuestion,
    indexDocument,
    clearMessages,
  };
}
