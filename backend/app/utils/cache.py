"""
Cache utilities — async Redis wrapper with JSON serialization.

Provides cache_get, cache_set, and cache_delete for working with
JSON-serialized values in Redis. Uses the shared persistent client.
"""

import json
from typing import Optional

from app.redis_client import get_client


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
        client = get_client()
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except RuntimeError:
        raise
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
        client = get_client()
        await client.set(key, json.dumps(value), ex=ttl)
    except RuntimeError:
        raise
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
        client = get_client()
        await client.delete(key)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Cache delete failed for key '{key}': {e}") from e
