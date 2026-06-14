"""Redis connection pool and async dependency for FastAPI."""

from typing import AsyncGenerator

import redis.asyncio as redis

from app.config import settings
from app.exceptions import AppException, REDIS_CONNECTION_ERROR

# Initialize pool eagerly from settings
pool: redis.ConnectionPool = redis.ConnectionPool.from_url(settings.REDIS_URL)


async def init_redis() -> None:
    """Re-initialize the Redis connection pool (e.g., for testing)."""
    global pool
    pool = redis.ConnectionPool.from_url(settings.REDIS_URL)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency that yields a Redis client from the connection pool.

    Wraps connection failures in AppException with REDIS_CONNECTION_ERROR.
    """
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
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
    finally:
        await client.aclose()
