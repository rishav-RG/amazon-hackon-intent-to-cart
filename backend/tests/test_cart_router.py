"""
Integration tests for cart router endpoints (PATCH /v1/cart, GET /v1/cart/{cartId}).

Uses httpx.AsyncClient with FastAPI ASGI transport and patches CartService
at the router module level for isolated endpoint testing.

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db
from app.models.cart import Cart_Model as Cart, CartItem
from tests.stubs.database import get_test_db

pytestmark = pytest.mark.asyncio

# Override the database dependency globally for all router tests
app.dependency_overrides[get_db] = get_test_db

BASE_URL = "http://testserver"
HEADERS = {"X-User-ID": "user-42"}

# Patch target for CartService in the router module
CART_SERVICE_PATH = "app.routers.cart.CartService"


def _make_cart(cart_id="cart-100", user_id="user-42", version=1, items=None):
    """Helper to create a Cart model instance for testing."""
    cart = Cart(id=cart_id, user_id=user_id, status="active", version=version)
    cart.items = items or []
    return cart


def _make_serialized_cart(cart_id="cart-100", version=1, items=None, total=0.0):
    """Helper to create a serialized cart dict matching CartResponse schema."""
    return {
        "cartId": cart_id,
        "version": version,
        "items": items or [],
        "total": total,
        "status": "active",
    }


# ---------------------------------------------------------------------------
# Test: PATCH /v1/cart with add operation → 200 with updated cart
# Validates: Requirement 4.1
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_cart_add_operation_returns_200():
    """PATCH /v1/cart with an add operation returns 200 with the updated cart."""
    existing_cart = _make_cart(version=1)
    updated_cart = _make_cart(version=2, items=[
        CartItem(cart_id="cart-100", product_id="prod-1", quantity=2, product_name="Test", price=5.0)
    ])
    serialized_updated = _make_serialized_cart(
        version=2,
        items=[{"productId": "prod-1", "quantity": 2, "price": 5.0}],
        total=10.0,
    )

    mock_service_instance = AsyncMock()
    mock_service_instance.get_by_user = AsyncMock(return_value=existing_cart)
    mock_service_instance.check_version = MagicMock(return_value=True)
    mock_service_instance.apply_operations = AsyncMock(return_value=updated_cart)
    mock_service_instance.save = AsyncMock(return_value=updated_cart)
    mock_service_instance._serialize = MagicMock(return_value=serialized_updated)

    with patch(CART_SERVICE_PATH) as MockCartService:
        MockCartService.return_value = mock_service_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
            response = await client.patch(
                "/v1/cart",
                json={
                    "operations": [{"type": "add", "productId": "prod-1", "quantity": 2}],
                    "version": 1,
                },
                headers=HEADERS,
            )

    assert response.status_code == 200
    data = response.json()
    assert data["cartId"] == "cart-100"
    assert data["version"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["productId"] == "prod-1"
    assert data["items"][0]["quantity"] == 2


# ---------------------------------------------------------------------------
# Test: PATCH /v1/cart with version conflict → 409
# Validates: Requirement 4.2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_cart_version_conflict_returns_409():
    """PATCH /v1/cart with stale version returns 409 Conflict."""
    existing_cart = _make_cart(version=5)
    serialized_existing = _make_serialized_cart(version=5)

    mock_service_instance = AsyncMock()
    mock_service_instance.get_by_user = AsyncMock(return_value=existing_cart)
    mock_service_instance.check_version = MagicMock(return_value=False)
    mock_service_instance._serialize = MagicMock(return_value=serialized_existing)

    with patch(CART_SERVICE_PATH) as MockCartService:
        MockCartService.return_value = mock_service_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
            response = await client.patch(
                "/v1/cart",
                json={
                    "operations": [{"type": "add", "productId": "prod-1", "quantity": 1}],
                    "version": 3,  # Stale version (server has 5)
                },
                headers=HEADERS,
            )

    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["message"] == "Version conflict"
    assert data["detail"]["serverVersion"] == 5


# ---------------------------------------------------------------------------
# Test: PATCH /v1/cart for new user creates cart automatically
# Validates: Requirement 4.3
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_cart_new_user_creates_cart():
    """PATCH /v1/cart for a user with no existing cart auto-creates one."""
    new_cart = _make_cart(cart_id="cart-new", version=0)
    saved_cart = _make_cart(cart_id="cart-new", version=1, items=[
        CartItem(cart_id="cart-new", product_id="prod-X", quantity=1, product_name="Test", price=5.0)
    ])
    serialized_saved = _make_serialized_cart(
        cart_id="cart-new",
        version=1,
        items=[{"productId": "prod-X", "quantity": 1, "price": 5.0}],
        total=5.0,
    )

    mock_service_instance = AsyncMock()
    mock_service_instance.get_by_user = AsyncMock(return_value=None)
    mock_service_instance.create = AsyncMock(return_value=new_cart)
    mock_service_instance.check_version = MagicMock(return_value=True)
    mock_service_instance.apply_operations = AsyncMock(return_value=saved_cart)
    mock_service_instance.save = AsyncMock(return_value=saved_cart)
    mock_service_instance._serialize = MagicMock(return_value=serialized_saved)

    with patch(CART_SERVICE_PATH) as MockCartService:
        MockCartService.return_value = mock_service_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
            response = await client.patch(
                "/v1/cart",
                json={
                    "operations": [{"type": "add", "productId": "prod-X", "quantity": 1}],
                },
                headers=HEADERS,
            )

    assert response.status_code == 200
    data = response.json()
    assert data["cartId"] == "cart-new"
    assert data["version"] == 1
    # Verify create was called since get_by_user returned None
    mock_service_instance.create.assert_awaited_once_with("user-42")


# ---------------------------------------------------------------------------
# Test: GET /v1/cart/{cartId} returns cart state
# Validates: Requirement 4.4
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cart_returns_cart_state():
    """GET /v1/cart/{cartId} returns the cart data with 200."""
    serialized_cart = _make_serialized_cart(
        cart_id="cart-200",
        version=3,
        items=[{"productId": "prod-A", "quantity": 5, "isSubstituted": False}],
        total=5.0,
    )

    mock_service_instance = AsyncMock()
    mock_service_instance.get = AsyncMock(return_value=serialized_cart)

    with patch(CART_SERVICE_PATH) as MockCartService:
        MockCartService.return_value = mock_service_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
            response = await client.get("/v1/cart/cart-200")

    assert response.status_code == 200
    data = response.json()
    assert data["cartId"] == "cart-200"
    assert data["version"] == 3
    assert len(data["items"]) == 1
    assert data["items"][0]["productId"] == "prod-A"
    assert data["items"][0]["quantity"] == 5
    assert data["status"] == "active"


# ---------------------------------------------------------------------------
# Test: GET /v1/cart/{cartId} for non-existent cart → 404
# Validates: Requirement 4.5
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cart_not_found_returns_404():
    """GET /v1/cart/{cartId} for a non-existent cart returns 404."""
    mock_service_instance = AsyncMock()
    mock_service_instance.get = AsyncMock(return_value=None)

    with patch(CART_SERVICE_PATH) as MockCartService:
        MockCartService.return_value = mock_service_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
            response = await client.get("/v1/cart/nonexistent-cart")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Cart not found"
