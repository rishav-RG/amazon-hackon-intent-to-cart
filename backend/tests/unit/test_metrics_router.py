"""Unit tests for app/routers/metrics.py — GET /v1/metrics endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.routers.metrics import router
from app.metrics import MetricsStore, metrics


def create_test_app() -> FastAPI:
    """Create a minimal FastAPI app with the metrics router for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def app() -> FastAPI:
    return create_test_app()


@pytest.fixture
def reset_metrics():
    """Reset singleton metrics counters before each test."""
    metrics.intent_count = 0
    metrics.bundle_count = 0
    metrics.cart_count = 0
    metrics.checkout_count = 0
    metrics.cache_hits = 0
    metrics.cache_checks = 0
    yield
    # Restore after test
    metrics.intent_count = 0
    metrics.bundle_count = 0
    metrics.cart_count = 0
    metrics.checkout_count = 0
    metrics.cache_hits = 0
    metrics.cache_checks = 0


@pytest.mark.asyncio
async def test_metrics_returns_200(app, reset_metrics):
    """GET /v1/metrics should return HTTP 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_returns_correct_keys(app, reset_metrics):
    """Response should contain all required fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/metrics")
    data = response.json()
    expected_keys = {"intent_count", "bundle_count", "cart_count", "checkout_count", "cache_hit_rate"}
    assert set(data.keys()) == expected_keys


@pytest.mark.asyncio
async def test_metrics_initial_values_are_zero(app, reset_metrics):
    """All counters should be zero initially."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/metrics")
    data = response.json()
    assert data["intent_count"] == 0
    assert data["bundle_count"] == 0
    assert data["cart_count"] == 0
    assert data["checkout_count"] == 0
    assert data["cache_hit_rate"] == 0.0


@pytest.mark.asyncio
async def test_metrics_reflects_incremented_counters(app, reset_metrics):
    """Endpoint should reflect updated counter values."""
    metrics.increment_intent()
    metrics.increment_intent()
    metrics.increment_bundle()
    metrics.increment_cart()
    metrics.increment_checkout()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/metrics")
    data = response.json()
    assert data["intent_count"] == 2
    assert data["bundle_count"] == 1
    assert data["cart_count"] == 1
    assert data["checkout_count"] == 1


@pytest.mark.asyncio
async def test_metrics_cache_hit_rate(app, reset_metrics):
    """Endpoint should compute and return correct cache_hit_rate."""
    metrics.record_cache_hit()   # 1 hit, 1 check
    metrics.record_cache_check()  # 0 hit, 1 check
    # Total: 1/2 = 0.5

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/metrics")
    data = response.json()
    assert data["cache_hit_rate"] == 0.5


@pytest.mark.asyncio
async def test_metrics_values_are_correct_types(app, reset_metrics):
    """Count fields are integers, cache_hit_rate is a float."""
    metrics.increment_intent()
    metrics.record_cache_hit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/metrics")
    data = response.json()
    assert isinstance(data["intent_count"], int)
    assert isinstance(data["bundle_count"], int)
    assert isinstance(data["cart_count"], int)
    assert isinstance(data["checkout_count"], int)
    assert isinstance(data["cache_hit_rate"], float)


@pytest.mark.asyncio
async def test_metrics_no_auth_required(app, reset_metrics):
    """Endpoint should not require authentication (no X-User-ID header)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/metrics")
    # Should succeed without any auth headers
    assert response.status_code == 200
