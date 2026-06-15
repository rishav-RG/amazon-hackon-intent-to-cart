"""
Unit tests for app.services.cart_service.CartService.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.cart import Cart_Model as Cart, CartItem
from app.services.cart_service import CartService
from app.events import _subscribers
from tests.stubs.database import create_mock_session
from tests.stubs.redis_client import FakeRedis

# The cache module imports get_redis from app.redis_client at the module level,
# so we patch the reference where it lives: app.utils.cache.get_redis
PATCH_GET_REDIS = "app.utils.cache.get_redis"


def _make_get_redis(fake_redis):
    """Create an async generator that yields the given FakeRedis instance."""
    async def _get_redis():
        yield fake_redis
    return _get_redis


@pytest.fixture(autouse=True)
def clear_event_subscribers():
    """Clear the global event subscribers between tests."""
    _subscribers.clear()
    yield
    _subscribers.clear()


@pytest.fixture
def fake_redis():
    """Provide a fresh FakeRedis instance for each test."""
    return FakeRedis()


@pytest.fixture
def mock_session():
    """Provide a fresh mock database session."""
    return create_mock_session()


@pytest.fixture
def cart_service(mock_session):
    """Provide a CartService with a mock session."""
    return CartService(db=mock_session)


# ---------------------------------------------------------------------------
# Test: create() initializes cart with correct user_id and version
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_initializes_cart(cart_service, mock_session, fake_redis):
    """create() should produce a Cart with the given user_id and version=0."""

    async def _get_redis():
        yield fake_redis

    with patch(PATCH_GET_REDIS, side_effect=_get_redis):
        cart = await cart_service.create(user_id="user-123", bundle_id="bundle-A")

    assert cart.user_id == "user-123"
    assert cart.bundle_id == "bundle-A"
    assert cart.version == 0
    assert cart.status == "active"
    mock_session.add.assert_called_once_with(cart)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(cart)


# ---------------------------------------------------------------------------
# Test: get() returns from cache when available
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_returns_from_cache(cart_service, fake_redis):
    """get() should return cached data without hitting the DB."""
    cached_data = {"cartId": "cart-1", "version": 2, "items": [], "total": 0, "status": "active"}
    fake_redis._store["cart:cart-1"] = json.dumps(cached_data)

    async def _get_redis():
        yield fake_redis

    with patch(PATCH_GET_REDIS, side_effect=_get_redis):
        result = await cart_service.get("cart-1")

    assert result == cached_data
    # DB should not have been called
    cart_service.db.execute.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test: get() falls back to DB when cache misses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_falls_back_to_db(mock_session, fake_redis):
    """get() should query DB when Redis has no cached entry."""
    # Create a Cart object the DB will return
    db_cart = Cart(id="cart-2", user_id="user-x", status="active", version=3)
    db_cart.items = [
        CartItem(cart_id="cart-2", product_id="prod-1", quantity=2, product_name="Test", price=5.0)
    ]

    # Configure mock session to return the cart
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = db_cart
    mock_session.execute.return_value = mock_result

    service = CartService(db=mock_session)

    async def _get_redis():
        yield fake_redis

    with patch(PATCH_GET_REDIS, side_effect=_get_redis):
        result = await service.get("cart-2")

    assert result is not None
    assert result["cartId"] == "cart-2"
    assert result["version"] == 3
    assert len(result["items"]) == 1
    assert result["items"][0]["productId"] == "prod-1"
    assert result["items"][0]["quantity"] == 2
    mock_session.execute.assert_awaited_once()

    # Verify that the result was cached
    cached_raw = fake_redis._store.get("cart:cart-2")
    assert cached_raw is not None
    assert json.loads(cached_raw) == result


# ---------------------------------------------------------------------------
# Test: apply_operations add/remove/update mutate cart correctly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_operations_add(cart_service):
    """apply_operations with 'add' should append a new item."""
    cart = Cart(id="cart-3", user_id="user-1", status="active", version=1)
    cart.items = []

    operations = [{"type": "add", "productId": "prod-A", "quantity": 3}]
    result = await cart_service.apply_operations(cart, operations)

    assert len(result.items) == 1
    assert result.items[0].product_id == "prod-A"
    assert result.items[0].quantity == 3


@pytest.mark.asyncio
async def test_apply_operations_remove(cart_service, mock_session):
    """apply_operations with 'remove' should remove the matching item."""
    item = CartItem(cart_id="cart-4", product_id="prod-B", quantity=1, product_name="Test", price=5.0)
    cart = Cart(id="cart-4", user_id="user-1", status="active", version=1)
    cart.items = [item]

    operations = [{"type": "remove", "productId": "prod-B"}]
    result = await cart_service.apply_operations(cart, operations)

    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_apply_operations_update(cart_service):
    """apply_operations with 'update' should change the item's quantity."""
    item = CartItem(cart_id="cart-5", product_id="prod-C", quantity=1, product_name="Test", price=5.0)
    cart = Cart(id="cart-5", user_id="user-1", status="active", version=1)
    cart.items = [item]

    operations = [{"type": "update", "productId": "prod-C", "quantity": 7}]
    result = await cart_service.apply_operations(cart, operations)

    assert result.items[0].quantity == 7


# ---------------------------------------------------------------------------
# Test: save() increments version and emits cart.updated event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_increments_version_and_emits_event(mock_session, fake_redis):
    """save() should increment version and emit cart.updated event."""
    from app.events import subscribe

    cart = Cart(id="cart-6", user_id="user-2", status="active", version=5)
    cart.items = []

    received_events = []

    async def handler(payload):
        received_events.append(payload)

    subscribe("cart.updated", handler)

    service = CartService(db=mock_session)

    async def _get_redis():
        yield fake_redis

    with patch(PATCH_GET_REDIS, side_effect=_get_redis):
        result = await service.save(cart)

    assert result.version == 6
    assert len(received_events) == 1
    assert received_events[0]["cart_id"] == "cart-6"
    assert received_events[0]["version"] == 6
    assert received_events[0]["item_count"] == 0


# ---------------------------------------------------------------------------
# Test: check_version rejects mismatched versions
# ---------------------------------------------------------------------------


def test_check_version_matches(cart_service):
    """check_version returns True when versions match."""
    cart = Cart(id="cart-7", user_id="user-3", status="active", version=4)
    cart.items = []
    assert cart_service.check_version(cart, 4) is True


def test_check_version_mismatch(cart_service):
    """check_version returns False when versions do not match."""
    cart = Cart(id="cart-8", user_id="user-3", status="active", version=4)
    cart.items = []
    assert cart_service.check_version(cart, 3) is False


def test_check_version_none_always_passes(cart_service):
    """check_version returns True when client_version is None."""
    cart = Cart(id="cart-9", user_id="user-3", status="active", version=99)
    cart.items = []
    assert cart_service.check_version(cart, None) is True
