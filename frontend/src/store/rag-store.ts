/**
 * VADP — RAG Zustand Store
 *
 * Client-side state management for active RAG research chat messages and citations.
 */

import { create } from "zustand";
import type { RAGQueryResponse, Citation } from "@/types/ai";

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  citations?: Citation[];
  timestamp: string;
  processingTimeMs?: number;
}

interface RAGState {
  messages: ChatMessage[];
  isLoading: boolean;
  activeCaseId: string | null;

  addMessage: (msg: ChatMessage) => void;
  setIsLoading: (loading: boolean) => void;
  setActiveCaseId: (caseId: string | null) => void;
  clearMessages: () => void;
}

export const useRAGStore = create<RAGState>((set) => ({
  messages: [],
  isLoading: false,
  activeCaseId: null,

  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setIsLoading: (isLoading) => set({ isLoading }),
  setActiveCaseId: (activeCaseId) => set({ activeCaseId }),
  clearMessages: () => set({ messages: [] }),
}));
