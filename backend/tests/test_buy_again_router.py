"""
Integration tests for the buy-again endpoint.

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.models.cart import CartItem
from tests.stubs.database import get_test_db

pytestmark = pytest.mark.asyncio

app.dependency_overrides[get_db] = get_test_db

HEADERS = {"X-User-ID": "user-1"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cart_item(product_id: str) -> CartItem:
    """Create a CartItem stub with the given product_id."""
    return CartItem(id=f"item-{product_id}", cart_id="cart-1", product_id=product_id, quantity=1, product_name="Test", price=5.0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@patch("app.routers.buy_again.cache_get", new_callable=AsyncMock)
async def test_buy_again_returns_cached_data(mock_cache_get):
    """GET /v1/buy-again returns cached data when available."""
    cached_items = [
        {"productId": "prod-1", "productName": "Widget", "lastOrderedAt": "2024-06-01T00:00:00Z"},
        {"productId": "prod-2", "productName": "Gadget", "lastOrderedAt": "2024-05-15T00:00:00Z"},
    ]
    mock_cache_get.return_value = cached_items

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/buy-again", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == cached_items
    mock_cache_get.assert_awaited_once_with("buy_again:user-1")


@patch("app.routers.buy_again.cache_set", new_callable=AsyncMock)
@patch("app.routers.buy_again.ProductCatalogAdapter")
@patch("app.routers.buy_again.cache_get", new_callable=AsyncMock)
async def test_buy_again_falls_back_to_db_and_populates_cache(
    mock_cache_get, mock_catalog, mock_cache_set
):
    """GET /v1/buy-again falls back to DB and populates cache on cache miss."""
    mock_cache_get.return_value = None

    # Configure catalog adapter response
    mock_catalog.get_products = AsyncMock(return_value={
        "prod-1": {"name": "Widget", "lastOrderedAt": "2024-06-01T00:00:00Z"},
        "prod-2": {"name": "Gadget", "lastOrderedAt": "2024-05-15T00:00:00Z"},
    })

    # Configure db session to return CartItems via dependency override
    cart_items = [_make_cart_item("prod-1"), _make_cart_item("prod-2")]
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = cart_items
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    async def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/v1/buy-again", headers=HEADERS)

        assert response.status_code == 200
        data = response.json()
        # Both products should be in the response
        product_ids = [item["productId"] for item in data]
        assert "prod-1" in product_ids
        assert "prod-2" in product_ids

        # Verify cache was populated
        mock_cache_set.assert_awaited_once()
        call_args = mock_cache_set.call_args
        assert call_args[0][0] == "buy_again:user-1"
        assert call_args[0][2] == 3600  # TTL
    finally:
        app.dependency_overrides[get_db] = get_test_db


@patch("app.routers.buy_again.cache_get", new_callable=AsyncMock)
async def test_buy_again_returns_empty_list_for_user_with_no_orders(mock_cache_get):
    """GET /v1/buy-again returns empty list for user with no checked-out carts."""
    mock_cache_get.return_value = None

    # DB returns empty results (default from get_test_db stub)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/buy-again", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == []
