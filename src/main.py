"""
VADP — FastAPI Application Entry Point
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
            {
                "name": "vadp",
                "description": "Verifiable AI Decision Provenance — Verification Contracts",
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

    # ── Root Route ───────────────────────────────────────────
    from fastapi.responses import HTMLResponse

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>VADP Backend REST API</title>
            <style>
                body { font-family: system-ui, -apple-system, sans-serif; background: #0a0a0f; color: #fff; display: flex; height: 100vh; margin: 0; align-items: center; justify-content: center; }
                .card { background: #12121e; border: 1px solid rgba(255,255,255,0.1); padding: 2.5rem; border-radius: 1rem; max-width: 500px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
                h1 { color: #818cf8; margin-top: 0; }
                p { color: #9ca3af; font-size: 0.95rem; line-height: 1.5; }
                .btn { display: inline-block; background: #4f46e5; color: #fff; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600; font-size: 0.875rem; margin: 0.5rem; }
                .btn-secondary { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); }
                .btn:hover { opacity: 0.9; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>VADP Backend Engine</h1>
                <p>FastAPI Zero Trust Legal AI Engine is running smoothly on <strong>port 8000</strong>.</p>
                <p>If you are looking for the web UI, please open the Next.js Frontend Portal at <strong>http://localhost:3000</strong>.</p>
                <div style="margin-top: 1.5rem;">
                    <a href="http://localhost:3000" class="btn">Open Frontend (Port 3000)</a>
                    <a href="/docs" class="btn btn-secondary">Interactive Swagger Docs</a>
                </div>
            </div>
        </body>
        </html>
        """

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
    from app.vadp.router import router as vadp_router

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
    app.include_router(vadp_router, prefix=settings.API_PREFIX)

    return app


# Create the application instance
app = create_app()
