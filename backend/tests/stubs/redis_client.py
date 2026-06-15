"""
In-memory Redis client mock for testing.

Provides an async-compatible mock that mimics the real Redis client interface
used by app/utils/cache.py (get, set, delete). Data is stored in a plain dict.
"""

from typing import Optional


class FakeRedis:
    """In-memory async Redis mock backed by a plain dict."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> Optional[str]:
        """Return the stored value for key, or None if missing."""
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        """Store value under key. TTL (ex) is accepted but ignored in tests."""
        self._store[key] = value

    async def delete(self, key: str) -> None:
        """Remove key from the store if it exists."""
        self._store.pop(key, None)


_instance: Optional[FakeRedis] = None


async def get_redis():
    """Yield a singleton FakeRedis instance (async generator to match real API)."""
    global _instance
    if _instance is None:
        _instance = FakeRedis()
    yield _instance
