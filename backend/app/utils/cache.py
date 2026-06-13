"""
Cache utilities — async Redis wrapper with JSON serialization.

Provides cache_get, cache_set, and cache_delete for working with
JSON-serialized values in Redis. All operations wrap exceptions
in RuntimeError with context information for debuggability.
"""

import json
from typing import Optional

from app.redis_client import get_redis


async def cache_get(key: str) -> Optional[dict]:
    """Retrieve and JSON-deserialize a value from Redis.

    Args:
        key: The Redis key to look up.

    Returns:
        The deserialized dict, or None if the key does not exist.

    Raises:
        RuntimeError: If the Redis operation fails.
    """
    try:
        redis = await get_redis()
        raw = await redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Cache read failed for key '{key}': {e}") from e


async def cache_set(key: str, value: dict, ttl: int) -> None:
    """JSON-serialize a value and store in Redis with TTL.

    Args:
        key: The Redis key to store under.
        value: The dict to JSON-serialize and store.
        ttl: Time-to-live in seconds.

    Raises:
        RuntimeError: If the Redis operation fails.
    """
    try:
        redis = await get_redis()
        await redis.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        raise RuntimeError(f"Cache write failed for key '{key}': {e}") from e


async def cache_delete(key: str) -> None:
    """Remove a key from Redis.

    Args:
        key: The Redis key to delete.

    Raises:
        RuntimeError: If the Redis operation fails.
    """
    try:
        redis = await get_redis()
        await redis.delete(key)
    except Exception as e:
        raise RuntimeError(f"Cache delete failed for key '{key}': {e}") from e
