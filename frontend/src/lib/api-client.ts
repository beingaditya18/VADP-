/**
 * VADP — API Client
 *
 * Type-safe API client wrapping fetch with:
 *   - Automatic JWT attachment from Supabase session
 *   - Consistent error handling
 *   - Request/response type inference
 *   - Retry logic with exponential backoff
 *
 * Usage:
 *   import { apiClient } from "@/lib/api-client";
 *
 *   const cases = await apiClient.get<CaseListResponse>("/cases");
 *   const newCase = await apiClient.post<Case>("/cases", { title: "..." });
 */

import type { ApiError } from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

/**
 * Custom error class for API errors.
 * Preserves the structured error response from the backend.
 */
export class ApiClientError extends Error {
  public readonly statusCode: number;
  public readonly errorCode: string;
  public readonly detail?: unknown;

  constructor(apiError: ApiError, statusCode: number) {
    super(apiError.message);
    this.name = "ApiClientError";
    this.statusCode = statusCode;
    this.errorCode = apiError.error_code;
    this.detail = apiError.detail;
  }
}

/**
 * Get the current access token.
 *
 * Lazily imports the Supabase client to avoid circular dependencies
 * and only accesses it client-side.
 */
async function getAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  try {
    const authStorage = localStorage.getItem("nyaya-auth-storage");
    if (authStorage) {
      const parsed = JSON.parse(authStorage);
      if (parsed?.state?.accessToken) {
        return parsed.state.accessToken;
      }
    }
    const { createBrowserClient } = await import("@/lib/supabase");
    const supabase = createBrowserClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  } catch {
    return null;
  }
}

/**
 * Sleep for a given number of milliseconds.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Core fetch wrapper with authentication, error handling, and retry logic.
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  retries: number = MAX_RETRIES
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  // Build headers
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json");

  // Attach JWT token
  const token = await getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  try {
    const response = await fetch(url, {
      ...options,
      credentials: "include",
      headers,
    });

    // Handle non-JSON responses (e.g., file downloads)
    const contentType = response.headers.get("Content-Type") || "";
    if (!contentType.includes("application/json")) {
      if (!response.ok) {
        throw new ApiClientError(
          {
            error: true,
            error_code: "NON_JSON_ERROR",
            message: `Request failed with status ${response.status}`,
          },
          response.status
        );
      }
      return response as unknown as T;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new ApiClientError(data as ApiError, response.status);
    }

    return data as T;
  } catch (error) {
    // Retry on network errors and 5xx server errors
    if (retries > 0 && shouldRetry(error)) {
      const delay = RETRY_DELAY_MS * (MAX_RETRIES - retries + 1);
      await sleep(delay);
      return request<T>(endpoint, options, retries - 1);
    }

    // Re-throw ApiClientError as-is
    if (error instanceof ApiClientError) {
      throw error;
    }

    // Wrap unexpected errors
    throw new ApiClientError(
      {
        error: true,
        error_code: "NETWORK_ERROR",
        message:
          error instanceof Error
            ? error.message
            : "An unexpected network error occurred.",
      },
      0
    );
  }
}

/**
 * Determine if a request should be retried.
 */
function shouldRetry(error: unknown): boolean {
  if (error instanceof ApiClientError) {
    return error.statusCode >= 500;
  }
  // Retry on network errors (TypeError: Failed to fetch)
  return error instanceof TypeError;
}

/**
 * Type-safe API client with methods for all HTTP verbs.
 */
export const apiClient = {
  /**
   * Send a GET request.
   */
  async get<T>(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined>
  ): Promise<T> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined) {
          searchParams.set(key, String(value));
        }
      }
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }
    return request<T>(url, { method: "GET" });
  },

  /**
   * Send a POST request with a JSON body.
   */
  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  /**
   * Send a PUT request with a JSON body.
   */
  async put<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  /**
   * Send a PATCH request with a JSON body.
   */
  async patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  /**
   * Send a DELETE request.
   */
  async delete<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: "DELETE" });
  },

  /**
   * Upload a file using multipart/form-data.
   */
  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    return request<T>(endpoint, {
      method: "POST",
      body: formData,
      // Don't set Content-Type — browser sets it with boundary for FormData
    });
  },
};
