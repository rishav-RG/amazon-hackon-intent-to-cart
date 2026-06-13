"""Health check endpoint.

Provides GET /health that verifies database and Redis connectivity
with 3-second timeouts for each check.

Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6
"""

import asyncio

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.redis_client import pool
from app.schemas.health import HealthResponse

import redis.asyncio as redis

router = APIRouter(tags=["health"])

_TIMEOUT_SECONDS = 3.0


async def _check_db() -> bool:
    """Check database connectivity by executing SELECT 1 with a 3s timeout."""
    try:
        async with AsyncSessionLocal() as session:
            await asyncio.wait_for(
                session.execute(text("SELECT 1")),
                timeout=_TIMEOUT_SECONDS,
            )
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    """Check Redis connectivity by executing PING with a 3s timeout."""
    try:
        client = redis.Redis(connection_pool=pool)
        try:
            await asyncio.wait_for(client.ping(), timeout=_TIMEOUT_SECONDS)
            return True
        finally:
            await client.aclose()
    except Exception:
        return False


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response) -> HealthResponse:
    """Return health status of the application.

    Checks database and Redis connectivity concurrently.
    Returns HTTP 200 if both are healthy, HTTP 503 otherwise.
    No authentication required.
    """
    db_ok, redis_ok = await asyncio.gather(_check_db(), _check_redis())

    db_status = "connected" if db_ok else "disconnected"
    redis_status = "connected" if redis_ok else "disconnected"
    overall_status = "healthy" if (db_ok and redis_ok) else "unhealthy"

    if overall_status == "unhealthy":
        response.status_code = 503

    return HealthResponse(
        status=overall_status,
        db=db_status,
        redis=redis_status,
    )
