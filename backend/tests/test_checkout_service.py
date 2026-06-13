"""
Unit tests for CheckoutService.

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.10
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.models.cart import Cart, CartItem
from app.services.checkout_service import (
    CheckoutService,
    CartNotActiveError,
    CartEmptyError,
    ItemsOutOfStockError,
)
from app.events import subscribe, _subscribers
from tests.stubs.database import create_mock_session
from tests.stubs.inventory_adapter import InventoryAdapter as StubInventoryAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cart(cart_id="cart-1", user_id="user-1", status="active", items=None):
    """Create a Cart instance with given attributes."""
    cart = Cart(id=cart_id, user_id=user_id, status=status, version=1)
    cart.items = items if items is not None else []
    return cart


def _make_cart_item(product_id="prod-1", quantity=1):
    """Create a CartItem instance."""
    return CartItem(id=f"item-{product_id}", cart_id="cart-1", product_id=product_id, quantity=quantity)


def _session_returning_cart(cart):
    """Create a mock session where execute().scalar_one_or_none() returns cart."""
    session = create_mock_session()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = cart
    session.execute.return_value = mock_result
    return session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_event_subscribers():
    """Clear event subscribers before and after each test."""
    _subscribers.clear()
    yield
    _subscribers.clear()


@pytest.fixture(autouse=True)
def reset_inventory_stub():
    """Reset inventory adapter stub between tests."""
    StubInventoryAdapter.reset()
    yield
    StubInventoryAdapter.reset()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rejects_cart_not_active():
    """Cart with status != 'active' raises CartNotActiveError."""
    cart = _make_cart(status="checked_out", items=[_make_cart_item()])
    session = _session_returning_cart(cart)

    svc = CheckoutService(db=session)

    with pytest.raises(CartNotActiveError):
        await svc.execute("cart-1", "user-1")


@pytest.mark.asyncio
async def test_rejects_empty_cart():
    """Active cart with no items raises CartEmptyError."""
    cart = _make_cart(status="active", items=[])
    session = _session_returning_cart(cart)

    svc = CheckoutService(db=session)

    with pytest.raises(CartEmptyError):
        await svc.execute("cart-1", "user-1")


@pytest.mark.asyncio
@patch("app.services.checkout_service.InventoryAdapter", StubInventoryAdapter)
@patch("app.services.checkout_service.OrderAdapter")
@patch("app.services.checkout_service.cache_delete", new_callable=AsyncMock)
async def test_raises_items_out_of_stock(mock_cache_delete, mock_order_adapter):
    """Returns OOS items when inventory check fails (raises ItemsOutOfStockError)."""
    cart = _make_cart(status="active", items=[_make_cart_item("prod-1"), _make_cart_item("prod-2")])
    session = _session_returning_cart(cart)

    # Configure stub to report prod-2 as out of stock with no substitutes
    StubInventoryAdapter._response = [
        {"product_id": "prod-1", "in_stock": True, "substitutes": []},
        {"product_id": "prod-2", "in_stock": False, "substitutes": []},
    ]

    svc = CheckoutService(db=session)

    with pytest.raises(ItemsOutOfStockError) as exc_info:
        await svc.execute("cart-1", "user-1")

    assert len(exc_info.value.oos_items) == 1
    assert exc_info.value.oos_items[0]["product_id"] == "prod-2"


@pytest.mark.asyncio
@patch("app.services.checkout_service.InventoryAdapter", StubInventoryAdapter)
@patch("app.services.checkout_service.OrderAdapter")
@patch("app.services.checkout_service.cache_delete", new_callable=AsyncMock)
async def test_successful_checkout_updates_cart_status(mock_cache_delete, mock_order_adapter):
    """Successful checkout updates cart status to 'checked_out'."""
    cart = _make_cart(status="active", items=[_make_cart_item("prod-1")])
    session = _session_returning_cart(cart)

    # OrderAdapter stub
    mock_order_adapter.place_order = AsyncMock(return_value={"orderId": "order-001", "total": 49.99})

    svc = CheckoutService(db=session)
    result = await svc.execute("cart-1", "user-1")

    assert cart.status == "checked_out"
    assert result["orderId"] == "order-001"
    session.commit.assert_awaited()


@pytest.mark.asyncio
@patch("app.services.checkout_service.InventoryAdapter", StubInventoryAdapter)
@patch("app.services.checkout_service.OrderAdapter")
@patch("app.services.checkout_service.cache_delete", new_callable=AsyncMock)
async def test_successful_checkout_emits_order_placed_event(mock_cache_delete, mock_order_adapter):
    """Successful checkout emits order.placed event."""
    cart = _make_cart(status="active", items=[_make_cart_item("prod-1")])
    session = _session_returning_cart(cart)

    mock_order_adapter.place_order = AsyncMock(return_value={"orderId": "order-002", "total": 29.99})

    # Subscribe handler to capture event
    captured_events = []

    async def handler(payload):
        captured_events.append(payload)

    subscribe("order.placed", handler)

    svc = CheckoutService(db=session)
    await svc.execute("cart-1", "user-1")

    assert len(captured_events) == 1
    assert captured_events[0]["order_id"] == "order-002"
    assert captured_events[0]["cart_id"] == "cart-1"
    assert captured_events[0]["user_id"] == "user-1"
    assert captured_events[0]["item_count"] == 1


@pytest.mark.asyncio
@patch("app.services.checkout_service.InventoryAdapter", StubInventoryAdapter)
@patch("app.services.checkout_service.OrderAdapter")
@patch("app.services.checkout_service.cache_delete", new_callable=AsyncMock)
async def test_successful_checkout_deletes_cart_cache(mock_cache_delete, mock_order_adapter):
    """Successful checkout deletes cart cache entry."""
    cart = _make_cart(status="active", items=[_make_cart_item("prod-1")])
    session = _session_returning_cart(cart)

    mock_order_adapter.place_order = AsyncMock(return_value={"orderId": "order-003", "total": 19.99})

    svc = CheckoutService(db=session)
    await svc.execute("cart-1", "user-1")

    mock_cache_delete.assert_awaited_once_with("cart:cart-1")
