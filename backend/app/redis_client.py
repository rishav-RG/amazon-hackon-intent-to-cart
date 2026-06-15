"""Redis connection — single persistent client reused across all requests."""

from typing import AsyncGenerator

import redis.asyncio as redis

from app.config import settings
from app.exceptions import AppException, REDIS_CONNECTION_ERROR

# Single persistent Redis client (initialized at startup)
_client: redis.Redis | None = None


async def init_redis() -> None:
    """Initialize the persistent Redis client from settings.REDIS_URL."""
    global _client
    _client = redis.from_url(settings.REDIS_URL, decode_responses=False)
    # Verify connection works at startup
    await _client.ping()


def get_client() -> redis.Redis:
    """Get the persistent Redis client. Must call init_redis() first."""
    if _client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() at startup.")
    return _client


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency that yields the shared Redis client.

    Wraps connection failures in AppException with REDIS_CONNECTION_ERROR.
    """
    if _client is None:
        raise AppException(
            error_code=REDIS_CONNECTION_ERROR[0],
            message="Redis not initialized",
            status_code=REDIS_CONNECTION_ERROR[1],
        )
    try:
        yield _client
    except redis.ConnectionError as exc:
        raise AppException(
            error_code=REDIS_CONNECTION_ERROR[0],
            message=f"Redis connection failed: {exc}",
            status_code=REDIS_CONNECTION_ERROR[1],
        ) from exc
    except redis.RedisError as exc:
        raise AppException(
            error_code=REDIS_CONNECTION_ERROR[0],
            message=f"Redis error: {exc}",
            status_code=REDIS_CONNECTION_ERROR[1],
        ) from exc


async def close_redis() -> None:
    """Close the Redis client on shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
