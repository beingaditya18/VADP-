"""
Nyaya-ZTA — FastAPI Application Entry Point
=============================================

Creates and configures the FastAPI application with:
  - Lifespan handler (startup/shutdown hooks)
  - All middleware (CORS, RequestID, Logging, RateLimit)
  - All routers (modules)
  - Global exception handlers
  - OpenAPI documentation configuration

Start the server:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import NyayaBaseException
from app.core.logging import get_logger, setup_logging
from app.core.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
)
from app.core.monitoring import router as health_router
from app.db.engine import dispose_engine
from app.db.init_db import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Startup:
      - Configure structured logging
      - Log application startup
      - Auto-initialize database tables if missing

    Shutdown:
      - Dispose database engine and close connections
      - Log application shutdown
    """
    settings = get_settings()

    # Configure logging
    setup_logging(
        level=settings.LOG_LEVEL.value,
        json_output=settings.is_production,
    )

    logger.info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT.value,
    )

    # Initialize database tables on startup (creates nyaya.db if missing)
    try:
        await init_db()
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e), exc_info=True)

    yield

    # Shutdown
    logger.info("Shutting down %s...", settings.APP_NAME)
    await dispose_engine()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """
    Application factory.

    Creates and fully configures the FastAPI application.
    This pattern allows creating fresh app instances for testing.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        # Custom OpenAPI metadata
        openapi_tags=[
            {
                "name": "monitoring",
                "description": "Health checks and application status",
            },
            {
                "name": "auth",
                "description": "Authentication and user management",
            },
            {
                "name": "authorization",
                "description": "Access control and policy management",
            },
            {
                "name": "cases",
                "description": "Judicial case management",
            },
            {
                "name": "documents",
                "description": "Document upload and management",
            },
            {
                "name": "evidence",
                "description": "Evidence verification and integrity",
            },
            {
                "name": "ai",
                "description": "AI recommendations and analysis",
            },
            {
                "name": "explainability",
                "description": "Explainable AI (SHAP, trust scores, explanations)",
            },
            {
                "name": "rag",
                "description": "Retrieval-Augmented Generation pipeline",
            },
            {
                "name": "ledger",
                "description": "Tamper-evident audit ledger",
            },
            {
                "name": "zero-trust",
                "description": "Zero Trust security assessment",
            },
            {
                "name": "search",
                "description": "Full-text and semantic search",
            },
            {
                "name": "notifications",
                "description": "User notification management",
            },
        ],
    )

    # ── Register Middleware (order matters: outermost first) ──

    # CORS — must be outermost to handle preflight requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # Request ID — assigns correlation ID to each request
    app.add_middleware(RequestIDMiddleware)

    # Request Logging — logs request/response with timing
    if settings.ENABLE_REQUEST_LOGGING:
        app.add_middleware(RequestLoggingMiddleware)

    # Rate Limiting — in-memory token bucket per IP
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    # ── Register Global Exception Handlers ───────────────────

    @app.exception_handler(NyayaBaseException)
    async def nyaya_exception_handler(
        request: Request, exc: NyayaBaseException
    ) -> JSONResponse:
        """Convert NyayaBaseException subclasses to consistent JSON responses."""
        logger.warning(
            "Application error: %s",
            exc.message,
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "path": request.url.path,
                "detail": exc.detail,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler for unhandled exceptions."""
        logger.error(
            "Unhandled exception: %s",
            str(exc),
            extra={"path": request.url.path},
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected internal error occurred.",
            },
        )

    # ── Register Routers ─────────────────────────────────────

    # Monitoring (no prefix — /health at root)
    app.include_router(health_router)

    # Authentication & Authorization Modules
    from app.auth.router import router as auth_router
    from app.authorization.router import router as authorization_router
    from app.cases.router import router as cases_router
    from app.documents.router import router as documents_router
    from app.evidence.router import router as evidence_router
    from app.ledger.router import router as ledger_router
    from app.rag.router import router as rag_router
    from app.ai.router import router as ai_router
    from app.notifications.router import router as notifications_router
    from app.search.router import router as search_router

    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(authorization_router, prefix=settings.API_PREFIX)
    app.include_router(cases_router, prefix=settings.API_PREFIX)
    app.include_router(documents_router, prefix=settings.API_PREFIX)
    app.include_router(evidence_router, prefix=settings.API_PREFIX)
    app.include_router(ledger_router, prefix=settings.API_PREFIX)
    app.include_router(rag_router, prefix=settings.API_PREFIX)
    app.include_router(ai_router, prefix=settings.API_PREFIX)
    app.include_router(notifications_router, prefix=settings.API_PREFIX)
    app.include_router(search_router, prefix=settings.API_PREFIX)

    return app


# Create the application instance
app = create_app()
