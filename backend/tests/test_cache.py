"""
Unit tests for app/utils/cache.py — cache_get, cache_set, cache_delete.

Validates: Requirements 2.1, 2.2, 2.3, 2.4
"""

import pytest
from unittest.mock import patch, AsyncMock

from tests.stubs.redis_client import get_redis as fake_get_redis, FakeRedis
from app.utils.cache import cache_get, cache_set, cache_delete


@pytest.fixture(autouse=True)
def reset_fake_redis():
    """Reset FakeRedis singleton store between tests."""
    import tests.stubs.redis_client as stub_module
    stub_module._instance = None
    yield


@pytest.mark.asyncio
@patch("app.utils.cache.get_redis", new=fake_get_redis)
async def test_cache_set_then_get_returns_original_value():
    """cache_set followed by cache_get returns the original dict value."""
    key = "user:123:cart"
    value = {"items": ["apple", "banana"], "total": 5.99}
    ttl = 300

    await cache_set(key, value, ttl)
    result = await cache_get(key)

    assert result == value


@pytest.mark.asyncio
@patch("app.utils.cache.get_redis", new=fake_get_redis)
async def test_cache_get_missing_key_returns_none():
    """cache_get on a non-existent key returns None."""
    result = await cache_get("nonexistent:key")

    assert result is None


@pytest.mark.asyncio
@patch("app.utils.cache.get_redis", new=fake_get_redis)
async def test_cache_delete_removes_key():
    """cache_delete removes the key so subsequent get returns None."""
    key = "session:abc"
    value = {"token": "xyz"}

    await cache_set(key, value, 60)
    await cache_delete(key)
    result = await cache_get(key)

    assert result is None


@pytest.mark.asyncio
async def test_cache_get_redis_error_raises_runtime_error():
    """Redis error on get propagates as RuntimeError with context."""
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = ConnectionError("Connection refused")

    async def failing_get_redis():
        yield mock_redis

    with patch("app.utils.cache.get_redis", new=failing_get_redis):
        with pytest.raises(RuntimeError, match="Cache read failed for key 'k1'"):
            await cache_get("k1")


@pytest.mark.asyncio
async def test_cache_set_redis_error_raises_runtime_error():
    """Redis error on set propagates as RuntimeError with context."""
    mock_redis = AsyncMock()
    mock_redis.set.side_effect = ConnectionError("Connection refused")

    async def failing_get_redis():
        yield mock_redis

    with patch("app.utils.cache.get_redis", new=failing_get_redis):
        with pytest.raises(RuntimeError, match="Cache write failed for key 'k2'"):
            await cache_set("k2", {"data": 1}, 60)


@pytest.mark.asyncio
async def test_cache_delete_redis_error_raises_runtime_error():
    """Redis error on delete propagates as RuntimeError with context."""
    mock_redis = AsyncMock()
    mock_redis.delete.side_effect = ConnectionError("Connection refused")

    async def failing_get_redis():
        yield mock_redis

    with patch("app.utils.cache.get_redis", new=failing_get_redis):
        with pytest.raises(RuntimeError, match="Cache delete failed for key 'k3'"):
            await cache_delete("k3")
