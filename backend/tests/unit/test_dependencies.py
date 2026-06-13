"""Unit tests for app/dependencies.py — User identity dependency."""

import pytest
from unittest.mock import MagicMock

from app.dependencies import get_current_user_id
from app.exceptions import AppException


def _make_request(headers: dict) -> MagicMock:
    """Create a mock Request with given headers."""
    request = MagicMock()
    request.headers = headers
    return request


@pytest.mark.asyncio
async def test_returns_user_id_when_valid():
    request = _make_request({"X-User-ID": "user-123"})
    result = await get_current_user_id(request)
    assert result == "user-123"


@pytest.mark.asyncio
async def test_returns_raw_value_with_surrounding_whitespace():
    """The function checks strip for validation but returns the raw value."""
    request = _make_request({"X-User-ID": "  user-456  "})
    result = await get_current_user_id(request)
    assert result == "  user-456  "


@pytest.mark.asyncio
async def test_raises_401_when_header_missing():
    request = _make_request({})
    with pytest.raises(AppException) as exc_info:
        await get_current_user_id(request)
    assert exc_info.value.error_code == "VALIDATION_ERROR"
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_raises_401_when_header_empty():
    request = _make_request({"X-User-ID": ""})
    with pytest.raises(AppException) as exc_info:
        await get_current_user_id(request)
    assert exc_info.value.error_code == "VALIDATION_ERROR"
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_raises_401_when_header_whitespace_only():
    request = _make_request({"X-User-ID": "   \t\n  "})
    with pytest.raises(AppException) as exc_info:
        await get_current_user_id(request)
    assert exc_info.value.error_code == "VALIDATION_ERROR"
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_error_message_mentions_header():
    request = _make_request({})
    with pytest.raises(AppException) as exc_info:
        await get_current_user_id(request)
    assert "X-User-ID" in exc_info.value.message
