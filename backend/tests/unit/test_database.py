"""Unit tests for app/database.py module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.database import engine, AsyncSessionLocal, get_db, dispose_engine
from app.exceptions import AppException, DB_CONNECTION_ERROR


def test_engine_exists():
    """Engine is created and not None."""
    assert engine is not None


def test_async_session_local_exists():
    """AsyncSessionLocal factory is created."""
    assert AsyncSessionLocal is not None


def test_async_session_local_expire_on_commit_false():
    """AsyncSessionLocal has expire_on_commit=False."""
    assert AsyncSessionLocal.kw.get("expire_on_commit") is False


@pytest.mark.asyncio
async def test_get_db_yields_session():
    """get_db yields a session object."""
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.database.AsyncSessionLocal", return_value=mock_session):
        gen = get_db()
        session = await gen.__anext__()
        assert session is mock_session

        # Cleanup - send None to advance past yield
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_get_db_wraps_connection_error():
    """get_db wraps connection exceptions in AppException with DB_CONNECTION_ERROR."""
    with patch(
        "app.database.AsyncSessionLocal",
        side_effect=ConnectionRefusedError("Connection refused"),
    ):
        gen = get_db()
        with pytest.raises(AppException) as exc_info:
            await gen.__anext__()

        assert exc_info.value.error_code == DB_CONNECTION_ERROR[0]
        assert exc_info.value.status_code == DB_CONNECTION_ERROR[1]
        assert "Database connection failed" in exc_info.value.message


@pytest.mark.asyncio
async def test_get_db_reraises_app_exception():
    """get_db re-raises AppException without wrapping."""
    original = AppException(
        error_code="SOME_ERROR", message="Original error", status_code=400
    )

    with patch("app.database.AsyncSessionLocal", side_effect=original):
        gen = get_db()
        with pytest.raises(AppException) as exc_info:
            await gen.__anext__()

        assert exc_info.value is original


@pytest.mark.asyncio
async def test_dispose_engine():
    """dispose_engine calls engine.dispose()."""
    with patch("app.database.engine") as mock_engine:
        mock_engine.dispose = AsyncMock()
        from app import database

        await database.dispose_engine()
        mock_engine.dispose.assert_called_once()
