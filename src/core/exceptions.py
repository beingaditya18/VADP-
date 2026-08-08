"""
VADP Exception Hierarchy
==============================

Defines a structured exception hierarchy for the entire application.
Each exception type maps to a specific HTTP status code and error category.
Global exception handlers (registered in main.py) convert these into
consistent JSON error responses.

Design Principles:
  - Every exception carries a machine-readable error_code for clients
  - All exceptions include optional detail for debugging
  - FastAPI global handlers ensure consistent response format
"""

from __future__ import annotations

from typing import Any


class NyayaBaseException(Exception):
    """
    Base exception for all VADP application errors.

    Attributes:
        status_code: HTTP status code to return.
        error_code: Machine-readable error identifier (e.g., "AUTH_TOKEN_EXPIRED").
        message: Human-readable error message.
        detail: Optional additional context for debugging.
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        detail: Any = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.detail = detail
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception to a JSON-compatible dictionary."""
        response: dict[str, Any] = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.detail is not None:
            response["detail"] = self.detail
        return response


# ── Authentication Errors ─────────────────────────────────────


class AuthenticationError(NyayaBaseException):
    """Raised when authentication fails (invalid/expired/missing credentials)."""

    status_code = 401
    error_code = "AUTH_FAILED"
    message = "Authentication failed."


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""

    error_code = "AUTH_TOKEN_EXPIRED"
    message = "Authentication token has expired. Please log in again."


class TokenInvalidError(AuthenticationError):
    """Raised when a JWT token is malformed or has an invalid signature."""

    error_code = "AUTH_TOKEN_INVALID"
    message = "Invalid authentication token."


# ── Authorization Errors ──────────────────────────────────────


class AuthorizationError(NyayaBaseException):
    """Raised when a user lacks permission for the requested operation."""

    status_code = 403
    error_code = "AUTHZ_DENIED"
    message = "You do not have permission to perform this action."


class InsufficientRoleError(AuthorizationError):
    """Raised when the user's role is insufficient."""

    error_code = "AUTHZ_INSUFFICIENT_ROLE"
    message = "Your role does not have access to this resource."


class PolicyViolationError(AuthorizationError):
    """Raised when an ABAC policy denies access."""

    error_code = "AUTHZ_POLICY_VIOLATION"
    message = "Access denied by security policy."


# ── Resource Errors ───────────────────────────────────────────


class NotFoundError(NyayaBaseException):
    """Raised when a requested resource does not exist."""

    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ConflictError(NyayaBaseException):
    """Raised when a resource conflict occurs (e.g., duplicate case number)."""

    status_code = 409
    error_code = "CONFLICT"
    message = "A resource conflict occurred."


# ── Validation Errors ─────────────────────────────────────────


class ValidationError(NyayaBaseException):
    """Raised when input validation fails beyond Pydantic's built-in checks."""

    status_code = 422
    error_code = "VALIDATION_FAILED"
    message = "Input validation failed."


class PromptInjectionError(ValidationError):
    """Raised when a prompt injection attack is detected."""

    error_code = "PROMPT_INJECTION_DETECTED"
    message = "Potential prompt injection detected. This attempt has been logged."


# ── Rate Limiting ─────────────────────────────────────────────


class RateLimitError(NyayaBaseException):
    """Raised when a client exceeds the rate limit."""

    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later."


# ── Ledger Errors ─────────────────────────────────────────────


class LedgerIntegrityError(NyayaBaseException):
    """Raised when the audit ledger integrity check fails (tampering detected)."""

    status_code = 500
    error_code = "LEDGER_INTEGRITY_VIOLATION"
    message = "Audit ledger integrity violation detected. Possible tampering."


class LedgerWriteError(NyayaBaseException):
    """Raised when writing to the ledger fails."""

    status_code = 500
    error_code = "LEDGER_WRITE_FAILED"
    message = "Failed to write to the audit ledger."


# ── AI / LLM Errors ──────────────────────────────────────────


class LLMServiceError(NyayaBaseException):
    """Raised when the LLM service is unavailable or returns an error."""

    status_code = 502
    error_code = "LLM_SERVICE_ERROR"
    message = "AI language model service is currently unavailable."


LLMError = LLMServiceError


class EmbeddingError(NyayaBaseException):
    """Raised when embedding generation fails."""

    status_code = 500
    error_code = "EMBEDDING_FAILED"
    message = "Failed to generate document embeddings."


class RAGPipelineError(NyayaBaseException):
    """Raised when the RAG pipeline encounters an error."""

    status_code = 500
    error_code = "RAG_PIPELINE_ERROR"
    message = "Retrieval-augmented generation pipeline error."


# ── External Service Errors ───────────────────────────────────


class ExternalServiceError(NyayaBaseException):
    """Raised when an external service (Supabase, storage, etc.) fails."""

    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "An external service is unavailable."


class StorageError(ExternalServiceError):
    """Raised when file storage operations fail."""

    error_code = "STORAGE_ERROR"
    message = "File storage operation failed."
