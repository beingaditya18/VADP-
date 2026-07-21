/**
 * Nyaya-ZTA — Case Types
 *
 * Type definitions for judicial case management.
 */

export type CaseStatus =
  | "filed"
  | "under_review"
  | "hearing"
  | "judgment"
  | "closed"
  | "appealed";

export type CasePriority = "low" | "medium" | "high" | "critical";

export type PartyType = "petitioner" | "respondent" | "witness" | "intervener";

export interface Case {
  id: string;
  case_number: string;
  title: string;
  description?: string;
  case_type: string;
  status: CaseStatus;
  priority: CasePriority;
  filed_by: string;
  assigned_judge?: string;
  assigned_lawyer?: string;
  court_id?: string;
  filing_date: string;
  next_hearing_date?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CaseParty {
  id: string;
  case_id: string;
  user_id?: string;
  party_name: string;
  party_type: PartyType;
  created_at: string;
}

export interface CaseEvent {
  id: string;
  case_id: string;
  event_type: string;
  description?: string;
  performed_by?: string;
  event_data: Record<string, unknown>;
  created_at: string;
}

export interface CaseCreateRequest {
  title: string;
  description?: string;
  case_type: string;
  priority?: CasePriority;
  parties?: Omit<CaseParty, "id" | "case_id" | "created_at">[];
}

export interface CaseUpdateRequest {
  title?: string;
  description?: string;
  status?: CaseStatus;
  priority?: CasePriority;
  assigned_judge?: string;
  assigned_lawyer?: string;
  next_hearing_date?: string;
}

export interface CaseListResponse {
  items: Case[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Document {
  id: string;
  case_id: string;
  uploaded_by: string;
  file_name: string;
  file_type?: string;
  file_size?: number;
  content_hash: string;
  is_verified: boolean;
  created_at: string;
}
