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
from app.redis_client import pool as redis_pool
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
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

    # Cart & Checkout routers (Dev C)
    app.include_router(cart.router)
    app.include_router(checkout.router)
    app.include_router(buy_again.router)

    # --- Shutdown Event ---

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Dispose database engine and close Redis pool on shutdown."""
        await dispose_engine()
        if redis_pool is not None:
            await redis_pool.aclose()

    return app


app = create_app()
