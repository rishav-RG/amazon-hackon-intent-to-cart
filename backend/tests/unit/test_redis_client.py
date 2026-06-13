"""Unit tests for app/redis_client.py — Redis connection pool and dependency."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import redis.asyncio as redis_async

from app.exceptions import AppException, REDIS_CONNECTION_ERROR


@pytest.mark.asyncio
async def test_init_redis_creates_pool():
    """init_redis() should create a ConnectionPool from settings.REDIS_URL."""
    from app import redis_client

    # Reset global pool state
    redis_client.pool = None

    with patch.object(redis_async.ConnectionPool, "from_url", return_value=MagicMock()) as mock_from_url:
        await redis_client.init_redis()
        mock_from_url.assert_called_once_with("redis://localhost:6379/0")
        assert redis_client.pool is not None


@pytest.mark.asyncio
async def test_get_redis_yields_client():
    """get_redis() should yield a Redis client and close it afterwards."""
    from app import redis_client

    mock_pool = MagicMock()
    redis_client.pool = mock_pool

    gen = redis_client.get_redis()
    client = await gen.__anext__()

    assert isinstance(client, redis_async.Redis)
    assert client.connection_pool is mock_pool

    # Finish the generator
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()


@pytest.mark.asyncio
async def test_get_redis_wraps_connection_error():
    """get_redis() should wrap redis.ConnectionError in AppException with REDIS_CONNECTION_ERROR."""
    from app import redis_client

    mock_pool = MagicMock()
    redis_client.pool = mock_pool

    gen = redis_client.get_redis()
    client = await gen.__anext__()

    # Simulate a ConnectionError being thrown into the generator
    with pytest.raises(AppException) as exc_info:
        await gen.athrow(redis_async.ConnectionError("Connection refused"))

    assert exc_info.value.error_code == REDIS_CONNECTION_ERROR[0]
    assert exc_info.value.status_code == REDIS_CONNECTION_ERROR[1]
    assert "Connection refused" in exc_info.value.message


@pytest.mark.asyncio
async def test_get_redis_wraps_generic_redis_error():
    """get_redis() should wrap redis.RedisError in AppException with REDIS_CONNECTION_ERROR."""
    from app import redis_client

    mock_pool = MagicMock()
    redis_client.pool = mock_pool

    gen = redis_client.get_redis()
    client = await gen.__anext__()

    with pytest.raises(AppException) as exc_info:
        await gen.athrow(redis_async.RedisError("Some redis error"))

    assert exc_info.value.error_code == REDIS_CONNECTION_ERROR[0]
    assert exc_info.value.status_code == 503
    assert "Some redis error" in exc_info.value.message
