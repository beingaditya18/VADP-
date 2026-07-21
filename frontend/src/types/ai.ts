/**
 * Nyaya-ZTA — AI & Explainability Types
 *
 * Type definitions for AI recommendations, SHAP explanations,
 * trust scores, and risk assessments.
 */

export type RecommendationStatus = "pending" | "approved" | "rejected" | "flagged";

export interface AIRecommendation {
  id: string;
  case_id: string;
  recommendation_type: string;
  recommendation_text: string;
  confidence_score: number;
  trust_score: number;
  risk_score: number;
  model_version?: string;
  llm_provider?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  processing_time_ms?: number;
  status: RecommendationStatus;
  reviewed_by?: string;
  reviewed_at?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  explanations?: AIExplanation[];
}

export interface SHAPExplanation {
  feature_name: string;
  shap_value: number;
  feature_value: number | string;
  contribution_direction: "positive" | "negative";
}

export interface AIExplanation {
  id: string;
  recommendation_id: string;
  explanation_type: string;
  shap_values: SHAPExplanation[];
  feature_importance: Record<string, number>;
  natural_language_explanation?: string;
  contributing_factors: ContributingFactor[];
  citations: Citation[];
  created_at: string;
}

export interface ContributingFactor {
  factor: string;
  impact: "high" | "medium" | "low";
  direction: "increases_risk" | "decreases_risk" | "neutral";
  explanation: string;
}

export interface Citation {
  document_id: string;
  document_name?: string;
  file_name: string;
  chunk_index: number;
  relevance_score: number;
  excerpt: string;
}

export interface RAGQueryResponse {
  query: string;
  answer: string;
  citations: Citation[];
  processing_time_ms: number;
  case_id?: string;
  created_at: string;
}

export interface TrustScoreBreakdown {
  overall: number;
  model_confidence: number;
  evidence_quality: number;
  source_reliability: number;
  consistency: number;
  weights: {
    alpha: number;
    beta: number;
    gamma: number;
    delta: number;
  };
}

export interface RiskAssessment {
  overall_score: number;
  features: RiskFeature[];
  risk_level: "low" | "medium" | "high" | "critical";
}

export interface RiskFeature {
  name: string;
  value: number;
  weight: number;
  contribution: number;
}

export interface CaseAnalysisResponse {
  case_id: string;
  summary: string;
  trust_score: number;
  risk_score: number;
  risk_level: string;
  recommendation: AIRecommendation;
  trust_breakdown: TrustScoreBreakdown;
  risk_assessment: RiskAssessment;
}
