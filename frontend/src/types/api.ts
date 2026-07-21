/**
 * Nyaya-ZTA — API Types
 *
 * Shared type definitions for API communication patterns.
 */

export interface ApiError {
  error: true;
  error_code: string;
  message: string;
  detail?: unknown;
}

export interface ApiSuccess<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface SearchParams extends PaginationParams {
  query?: string;
  filters?: Record<string, string | string[]>;
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

/**
 * Type guard to check if an API response is an error.
 */
export function isApiError<T>(response: ApiResponse<T>): response is ApiError {
  return "error" in response && response.error === true;
}
