"""
Application factory for Intent-to-Cart backend.

Creates and configures the FastAPI application with middleware,
exception handlers, routers, and shutdown hooks.

Validates: Requirements 4.2, 4.4, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7,
           22.1, 22.2, 22.3, 22.4, 22.5
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import dispose_engine
from app.exceptions import AppException
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import RequestTimingMiddleware
from app.redis_client import init_redis, close_redis
from app.routers import clarification, health, intent, metrics
from app.routers import cart, checkout, buy_again

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance.

    - Registers exception handlers for AppException and generic Exception
    - Attaches middleware: RequestIDMiddleware, RequestTimingMiddleware, CORSMiddleware
    - Registers routers: health, intent, clarification, metrics, cart, checkout, buy_again
    - Registers shutdown event for cleanup
    """
    app = FastAPI(
        title="Intent-to-Cart",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
    )

    # --- Exception Handlers ---

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Convert AppException to structured JSON error response."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions without exposing internals."""
        logger.exception("Unhandled exception during request processing")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )

    # --- Middleware (LIFO order: last added = outermost) ---

    # CORSMiddleware added first (innermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-User-ID", "X-Request-ID"],
        allow_credentials=True,
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # RequestTimingMiddleware added second (middle)
    app.add_middleware(RequestTimingMiddleware)

    # RequestIDMiddleware added last (outermost)
    app.add_middleware(RequestIDMiddleware)

    # --- Routers ---

    app.include_router(health.router)
    app.include_router(intent.router)
    app.include_router(clarification.router)
    app.include_router(metrics.router)

    # Bundle router (Dev B)
    from app.routers import bundles
    app.include_router(bundles.router)

    # Cart & Checkout routers (Dev C)
    app.include_router(cart.router)
    app.include_router(checkout.router)
    app.include_router(buy_again.router)

    # --- Shutdown Event ---

    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize Redis, warm DB pool, and pre-load category embeddings."""
        await init_redis()
        # Pre-warm DB connection (Neon cold start can take 5-10s)
        from app.database import AsyncSessionLocal
        from sqlalchemy import text
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            logger.info("Database connection pool warmed up")
        except Exception as exc:
            logger.warning("DB warm-up failed (will retry on first request): %s", exc)
        # Pre-load category embeddings for the hybrid Category Resolver
        try:
            from app.services import category_resolver
            category_resolver.warmup()
        except Exception as exc:
            logger.warning("CategoryResolver warmup failed: %s", exc)

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Dispose database engine and close Redis client on shutdown."""
        await dispose_engine()
        await close_redis()

    return app


app = create_app()
