"""
Integration tests for POST /v1/checkout endpoint.

Validates: Requirements 6.1, 6.2, 6.3, 6.4
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from tests.stubs.database import get_test_db
from app.services.checkout_service import (
    CartNotActiveError,
    CartEmptyError,
    ItemsOutOfStockError,
)

pytestmark = pytest.mark.asyncio

app.dependency_overrides[get_db] = get_test_db


@pytest.fixture
def checkout_url():
    return "/v1/checkout"


@pytest.fixture
def valid_body():
    return {"cartId": "cart-123"}


@pytest.fixture
def user_headers():
    return {"X-User-ID": "user-1"}


async def test_checkout_valid_cart_returns_200(checkout_url, valid_body, user_headers):
    """POST /v1/checkout with valid cart returns 200 confirmed."""
    mock_result = {
        "orderId": "order-1",
        "status": "confirmed",
        "items": [{"productId": "p1", "quantity": 2, "price": 9.99}],
        "total": 19.98,
    }

    with patch("app.routers.checkout.CheckoutService") as MockService:
        instance = MockService.return_value
        instance.execute = AsyncMock(return_value=mock_result)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                checkout_url, json=valid_body, headers=user_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert data["orderId"] == "order-1"
    assert data["status"] == "confirmed"
    assert data["items"] == [{"productId": "p1", "quantity": 2, "price": 9.99}]
    assert data["total"] == 19.98


async def test_checkout_inactive_cart_returns_400(checkout_url, valid_body, user_headers):
    """POST /v1/checkout with inactive cart returns 400."""
    with patch("app.routers.checkout.CheckoutService") as MockService:
        instance = MockService.return_value
        instance.execute = AsyncMock(
            side_effect=CartNotActiveError("Cart not active")
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                checkout_url, json=valid_body, headers=user_headers
            )

    assert response.status_code == 400
    assert "Cart not active" in response.json()["detail"]


async def test_checkout_empty_cart_returns_400(checkout_url, valid_body, user_headers):
    """POST /v1/checkout with empty cart returns 400."""
    with patch("app.routers.checkout.CheckoutService") as MockService:
        instance = MockService.return_value
        instance.execute = AsyncMock(
            side_effect=CartEmptyError("Cart has no items")
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                checkout_url, json=valid_body, headers=user_headers
            )

    assert response.status_code == 400
    assert "Cart has no items" in response.json()["detail"]


async def test_checkout_oos_items_returns_422(checkout_url, valid_body, user_headers):
    """POST /v1/checkout with out-of-stock items returns 422 with item details."""
    oos_items = [{"product_id": "p1", "in_stock": False}]

    with patch("app.routers.checkout.CheckoutService") as MockService:
        instance = MockService.return_value
        instance.execute = AsyncMock(
            side_effect=ItemsOutOfStockError(oos_items)
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                checkout_url, json=valid_body, headers=user_headers
            )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "ITEMS_OUT_OF_STOCK"
    assert detail["items"] == oos_items
