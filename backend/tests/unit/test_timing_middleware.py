"""
Unit tests for the Request Timing Middleware.

Validates requirements 18.1, 18.2, 18.3, 18.4.
"""

import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.middleware.timing import RequestTimingMiddleware


@pytest.fixture
def app_with_timing():
    """Create a minimal FastAPI app with the timing middleware."""
    app = FastAPI()
    app.add_middleware(RequestTimingMiddleware)

    @app.get("/success")
    async def success_endpoint():
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint():
        raise RuntimeError("Unhandled exception")

    @app.get("/not-found")
    async def not_found_endpoint():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")

    return app


@pytest.mark.asyncio
async def test_adds_x_process_time_header(app_with_timing):
    """Requirement 18.3: X-Process-Time header is added to response."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_timing), base_url="http://test"
    ) as client:
        response = await client.get("/success")

    assert response.status_code == 200
    assert "x-process-time" in response.headers
    # Verify it's a valid float string
    duration = float(response.headers["x-process-time"])
    assert duration >= 0


@pytest.mark.asyncio
async def test_duration_rounded_to_2_decimal_places(app_with_timing):
    """Requirement 18.1: Duration is rounded to 2 decimal places."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_timing), base_url="http://test"
    ) as client:
        response = await client.get("/success")

    duration_str = response.headers["x-process-time"]
    # If there's a decimal point, verify at most 2 decimal places
    if "." in duration_str:
        decimal_part = duration_str.split(".")[1]
        assert len(decimal_part) <= 2


@pytest.mark.asyncio
async def test_logs_info_on_success(app_with_timing, caplog):
    """Requirement 18.2: Logs INFO with method, path, status code, duration_ms."""
    with caplog.at_level(logging.INFO, logger="app.middleware.timing"):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_timing), base_url="http://test"
        ) as client:
            await client.get("/success")

    # Find log record from our middleware
    timing_logs = [r for r in caplog.records if r.name == "app.middleware.timing"]
    assert len(timing_logs) == 1
    log_message = timing_logs[0].message
    assert "GET" in log_message
    assert "/success" in log_message
    assert "200" in log_message
    assert "ms" in log_message


@pytest.mark.asyncio
async def test_handles_exception_with_header_and_log(app_with_timing, caplog):
    """Requirement 18.4: On unhandled exception, still logs and adds header."""
    with caplog.at_level(logging.INFO, logger="app.middleware.timing"):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_timing), base_url="http://test"
        ) as client:
            response = await client.get("/error")

    # Should get a 500 response
    assert response.status_code == 500
    # Should still have the timing header
    assert "x-process-time" in response.headers
    duration = float(response.headers["x-process-time"])
    assert duration >= 0

    # Should have logged the error
    timing_logs = [r for r in caplog.records if r.name == "app.middleware.timing"]
    assert len(timing_logs) == 1
    log_message = timing_logs[0].message
    assert "GET" in log_message
    assert "/error" in log_message
    assert "500" in log_message
    assert "ms" in log_message


@pytest.mark.asyncio
async def test_logs_correct_status_for_http_exceptions(app_with_timing, caplog):
    """Verify that non-500 error responses also get timed correctly."""
    with caplog.at_level(logging.INFO, logger="app.middleware.timing"):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_timing), base_url="http://test"
        ) as client:
            response = await client.get("/not-found")

    assert response.status_code == 404
    assert "x-process-time" in response.headers

    timing_logs = [r for r in caplog.records if r.name == "app.middleware.timing"]
    assert len(timing_logs) == 1
    log_message = timing_logs[0].message
    assert "404" in log_message
