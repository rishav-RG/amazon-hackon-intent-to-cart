"""
Tests for Developer B's adapter implementations.
Tests all 4 adapters: Inventory, ETA, Order, Catalog.
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock

from app.adapters.inventory_adapter import InventoryAdapter
from app.adapters.eta_adapter import ETAAdapter
from app.adapters.order_adapter import OrderAdapter
from app.adapters.catalog_adapter import ProductCatalogAdapter


# ========================================
# InventoryAdapter Tests
# ========================================

@pytest.mark.asyncio
async def test_inventory_check_batch_returns_all_products():
    """Every requested product_id must appear in the result."""
    adapter = InventoryAdapter()
    ids = ["prod-001", "prod-002", "prod-003"]
    result = await adapter.check_batch(ids)
    assert set(result.keys()) == set(ids)


@pytest.mark.asyncio
async def test_inventory_result_shape():
    """Each entry must have 'available' (bool) and 'warehouse' (str)."""
    adapter = InventoryAdapter()
    result = await adapter.check_batch(["prod-001"])
    entry = result["prod-001"]
    assert isinstance(entry["available"], bool)
    assert isinstance(entry["warehouse"], str)
    assert entry["warehouse"].startswith("WH-")


@pytest.mark.asyncio
async def test_inventory_oos_rate_roughly_respected():
    """With 1000 products, OOS rate should be near MOCK_INVENTORY_OOS_RATE."""
    adapter = InventoryAdapter()
    ids = [f"prod-{i:04d}" for i in range(1000)]
    result = await adapter.check_batch(ids)
    oos_count = sum(1 for v in result.values() if not v["available"])
    oos_rate = oos_count / 1000
    # Allow wide tolerance — it's random
    assert 0.02 < oos_rate < 0.40, f"OOS rate {oos_rate} outside acceptable range"


@pytest.mark.asyncio
async def test_inventory_empty_list():
    """Empty input must return empty dict, not raise."""
    adapter = InventoryAdapter()
    result = await adapter.check_batch([])
    assert result == {}


@pytest.mark.asyncio
async def test_inventory_warehouse_values():
    """Warehouse values should be from predefined list."""
    adapter = InventoryAdapter()
    result = await adapter.check_batch([f"prod-{i}" for i in range(100)])
    warehouses = {v["warehouse"] for v in result.values()}
    assert warehouses.issubset({"WH-A", "WH-B", "WH-C"})


# ========================================
# ETAAdapter Tests
# ========================================

@pytest.mark.asyncio
async def test_eta_get_batch_returns_all_products():
    adapter = ETAAdapter()
    ids = ["prod-001", "prod-002"]
    result = await adapter.get_batch(ids)
    assert set(result.keys()) == set(ids)


@pytest.mark.asyncio
async def test_eta_result_shape():
    adapter = ETAAdapter()
    result = await adapter.get_batch(["prod-001"])
    entry = result["prod-001"]
    assert isinstance(entry["eta_minutes"], int)
    assert isinstance(entry["eta_label"], str)
    assert str(entry["eta_minutes"]) in entry["eta_label"]


@pytest.mark.asyncio
async def test_eta_minutes_within_config_range():
    from app.config import get_settings
    settings = get_settings()
    adapter = ETAAdapter()
    ids = [f"p-{i}" for i in range(200)]
    result = await adapter.get_batch(ids)
    for entry in result.values():
        assert settings.MOCK_ETA_MIN_MINUTES <= entry["eta_minutes"] <= settings.MOCK_ETA_MAX_MINUTES


@pytest.mark.asyncio
async def test_eta_empty_list():
    """Empty input must return empty dict, not raise."""
    adapter = ETAAdapter()
    result = await adapter.get_batch([])
    assert result == {}


@pytest.mark.asyncio
async def test_eta_accepts_warehouse_parameter():
    """Warehouse parameter should be accepted without error."""
    adapter = ETAAdapter()
    result = await adapter.get_batch(["prod-001"], warehouse="WH-B")
    assert "prod-001" in result


# ========================================
# OrderAdapter Tests
# ========================================

@pytest.mark.asyncio
async def test_order_adapter_returns_confirmed():
    adapter = OrderAdapter()
    result = await adapter.place_order("user-1", [{"product_id": "p1", "quantity": 2}])
    assert result["status"] == "confirmed"
    assert result["orderId"].startswith("ORD-")
    assert len(result["orderId"]) == 12  # "ORD-" + 8 hex chars


@pytest.mark.asyncio
async def test_order_adapter_unique_order_ids():
    """Two calls must produce different order IDs."""
    adapter = OrderAdapter()
    r1 = await adapter.place_order("user-1", [])
    r2 = await adapter.place_order("user-1", [])
    assert r1["orderId"] != r2["orderId"]


@pytest.mark.asyncio
async def test_order_adapter_50ms_delay():
    """Should have at least 50ms delay to simulate external API."""
    import time
    adapter = OrderAdapter()
    start = time.monotonic()
    await adapter.place_order("user-1", [])
    elapsed = time.monotonic() - start
    assert elapsed >= 0.05, f"Expected >=50ms delay, got {elapsed*1000:.1f}ms"


@pytest.mark.asyncio
async def test_order_adapter_empty_items():
    """Should handle empty items list without error."""
    adapter = OrderAdapter()
    result = await adapter.place_order("user-1", [])
    assert result["status"] == "confirmed"


# ========================================
# ProductCatalogAdapter Tests
# ========================================

@pytest.mark.asyncio
async def test_catalog_adapter_empty_list():
    """Empty input should return empty list."""
    adapter = ProductCatalogAdapter()
    result = await adapter.get_products([])
    assert result == []


@pytest.mark.asyncio
async def test_catalog_adapter_unknown_ids():
    """Unknown product IDs should return empty list."""
    adapter = ProductCatalogAdapter()
    result = await adapter.get_products(["unknown-001", "unknown-002"])
    assert result == []


@pytest.mark.asyncio
async def test_catalog_adapter_returns_list():
    """Should return a list (even if empty before Phase 2)."""
    adapter = ProductCatalogAdapter()
    result = await adapter.get_products(["mp-001"])
    assert isinstance(result, list)


# Note: Full catalog adapter tests will be added in Phase 2
# when MOCK_CATALOG is available in bundle_generator.py
