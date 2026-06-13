"""
Test suite for all mock adapters (Phase 1).

Tests Dev B's mock implementations:
- InventoryAdapter: Stock checking with OOS simulation
- ETAAdapter: Delivery time estimation
- OrderAdapter: Order placement
- ProductCatalogAdapter: Product metadata lookup
"""

import pytest
from unittest.mock import patch, MagicMock


# Mock settings before importing adapters
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests to avoid requiring .env file."""
    mock_config = MagicMock()
    mock_config.MOCK_INVENTORY_OOS_RATE = 0.15
    mock_config.MOCK_ETA_MIN_MINUTES = 20
    mock_config.MOCK_ETA_MAX_MINUTES = 90
    
    with patch('app.adapters.inventory_adapter.settings', mock_config), \
         patch('app.adapters.eta_adapter.settings', mock_config):
        yield mock_config


from app.adapters.inventory_adapter import InventoryAdapter
from app.adapters.eta_adapter import ETAAdapter
from app.adapters.order_adapter import OrderAdapter
from app.adapters.catalog_adapter import ProductCatalogAdapter


# ============================================================================
# InventoryAdapter Tests
# ============================================================================

@pytest.mark.asyncio
async def test_inventory_adapter_returns_correct_structure():
    """InventoryAdapter.check_batch() returns dict[str, dict] with required keys."""
    product_ids = ["prod-001", "prod-002", "prod-003"]
    
    result = await InventoryAdapter.check_batch(product_ids)
    
    assert isinstance(result, dict)
    assert len(result) == 3
    
    for product_id in product_ids:
        assert product_id in result
        assert "available" in result[product_id]
        assert "warehouse" in result[product_id]
        assert isinstance(result[product_id]["available"], bool)
        assert isinstance(result[product_id]["warehouse"], str)


@pytest.mark.asyncio
async def test_inventory_adapter_warehouse_values():
    """InventoryAdapter assigns one of three valid warehouses."""
    product_ids = ["prod-001", "prod-002", "prod-003"]
    valid_warehouses = {"WH-A", "WH-B", "WH-C"}
    
    result = await InventoryAdapter.check_batch(product_ids)
    
    for product_id, info in result.items():
        assert info["warehouse"] in valid_warehouses


@pytest.mark.asyncio
async def test_inventory_adapter_respects_oos_rate():
    """InventoryAdapter marks approximately MOCK_INVENTORY_OOS_RATE as unavailable."""
    # Run large batch to get statistical significance
    product_ids = [f"prod-{i:03d}" for i in range(100)]
    
    result = await InventoryAdapter.check_batch(product_ids)
    
    unavailable_count = sum(
        1 for info in result.values() if not info["available"]
    )
    unavailable_rate = unavailable_count / 100
    
    # Should be approximately 15% OOS (allow 5-25% range for randomness)
    assert 0.05 <= unavailable_rate <= 0.25


@pytest.mark.asyncio
async def test_inventory_adapter_empty_input():
    """InventoryAdapter handles empty product list gracefully."""
    result = await InventoryAdapter.check_batch([])
    
    assert result == {}


@pytest.mark.asyncio
async def test_inventory_adapter_single_product():
    """InventoryAdapter works with single product."""
    result = await InventoryAdapter.check_batch(["prod-001"])
    
    assert len(result) == 1
    assert "prod-001" in result


# ============================================================================
# ETAAdapter Tests
# ============================================================================

@pytest.mark.asyncio
async def test_eta_adapter_returns_correct_structure():
    """ETAAdapter.get_batch() returns dict[str, dict] with required keys."""
    product_ids = ["prod-001", "prod-002", "prod-003"]
    
    result = await ETAAdapter.get_batch(product_ids)
    
    assert isinstance(result, dict)
    assert len(result) == 3
    
    for product_id in product_ids:
        assert product_id in result
        assert "eta_minutes" in result[product_id]
        assert "eta_label" in result[product_id]
        assert isinstance(result[product_id]["eta_minutes"], int)
        assert isinstance(result[product_id]["eta_label"], str)


@pytest.mark.asyncio
async def test_eta_adapter_respects_time_range():
    """ETAAdapter generates ETAs within configured min/max range."""
    product_ids = [f"prod-{i:03d}" for i in range(20)]
    
    result = await ETAAdapter.get_batch(product_ids)
    
    for info in result.values():
        eta_minutes = info["eta_minutes"]
        # Default config: 20-90 minutes
        assert 20 <= eta_minutes <= 90


@pytest.mark.asyncio
async def test_eta_adapter_label_format():
    """ETAAdapter generates correct label format."""
    product_ids = ["prod-001"]
    
    result = await ETAAdapter.get_batch(product_ids)
    
    eta_minutes = result["prod-001"]["eta_minutes"]
    eta_label = result["prod-001"]["eta_label"]
    
    assert eta_label == f"In {eta_minutes} min"


@pytest.mark.asyncio
async def test_eta_adapter_empty_input():
    """ETAAdapter handles empty product list gracefully."""
    result = await ETAAdapter.get_batch([])
    
    assert result == {}


@pytest.mark.asyncio
async def test_eta_adapter_single_product():
    """ETAAdapter works with single product."""
    result = await ETAAdapter.get_batch(["prod-001"])
    
    assert len(result) == 1
    assert "prod-001" in result


# ============================================================================
# OrderAdapter Tests
# ============================================================================

@pytest.mark.asyncio
async def test_order_adapter_returns_correct_structure():
    """OrderAdapter.place_order() returns dict with required keys."""
    user_id = "user-123"
    items = [
        {"product_id": "prod-001", "quantity": 2, "unit_price": 5.99},
        {"product_id": "prod-002", "quantity": 1, "unit_price": 12.49}
    ]
    
    result = await OrderAdapter.place_order(user_id, items)
    
    assert isinstance(result, dict)
    assert "order_id" in result
    assert "status" in result
    assert "user_id" in result
    assert "total_items" in result


@pytest.mark.asyncio
async def test_order_adapter_generates_unique_order_ids():
    """OrderAdapter generates unique order IDs for each call."""
    user_id = "user-123"
    items = [{"product_id": "prod-001", "quantity": 1, "unit_price": 5.99}]
    
    result1 = await OrderAdapter.place_order(user_id, items)
    result2 = await OrderAdapter.place_order(user_id, items)
    
    assert result1["order_id"] != result2["order_id"]
    assert result1["order_id"].startswith("ORD-")
    assert result2["order_id"].startswith("ORD-")


@pytest.mark.asyncio
async def test_order_adapter_returns_confirmed_status():
    """OrderAdapter mock always returns confirmed status."""
    user_id = "user-123"
    items = [{"product_id": "prod-001", "quantity": 1, "unit_price": 5.99}]
    
    result = await OrderAdapter.place_order(user_id, items)
    
    assert result["status"] == "confirmed"


@pytest.mark.asyncio
async def test_order_adapter_preserves_user_id():
    """OrderAdapter includes correct user_id in response."""
    user_id = "user-456"
    items = [{"product_id": "prod-001", "quantity": 1, "unit_price": 5.99}]
    
    result = await OrderAdapter.place_order(user_id, items)
    
    assert result["user_id"] == user_id


@pytest.mark.asyncio
async def test_order_adapter_counts_items_correctly():
    """OrderAdapter returns correct total_items count."""
    user_id = "user-123"
    items = [
        {"product_id": "prod-001", "quantity": 2, "unit_price": 5.99},
        {"product_id": "prod-002", "quantity": 1, "unit_price": 12.49},
        {"product_id": "prod-003", "quantity": 3, "unit_price": 8.00}
    ]
    
    result = await OrderAdapter.place_order(user_id, items)
    
    assert result["total_items"] == 3


# ============================================================================
# ProductCatalogAdapter Tests
# ============================================================================

@pytest.mark.asyncio
async def test_catalog_adapter_returns_list():
    """ProductCatalogAdapter.get_products() returns list (Phase 1: empty)."""
    product_ids = ["prod-001", "prod-002"]
    
    result = await ProductCatalogAdapter.get_products(product_ids)
    
    assert isinstance(result, list)
    # Phase 1: Returns empty list (catalog added in Phase 2)
    assert result == []


@pytest.mark.asyncio
async def test_catalog_adapter_empty_input():
    """ProductCatalogAdapter handles empty product list."""
    result = await ProductCatalogAdapter.get_products([])
    
    assert isinstance(result, list)
    assert result == []
