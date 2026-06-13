"""
Tests for SubstitutionEngine - Out-of-stock product replacement logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.substitution_engine import SubstitutionEngine, CONFIDENCE_AUTO_REPLACE_THRESHOLD
from app.schemas.bundle import BundleSchema, BundleItemSchema


def _make_bundle_with_item(
    product_id: str,
    available: bool = True,
    name: str = "Test Product",
    unit_price: float = 100.0,
    quantity: int = 1,
) -> tuple[BundleSchema, dict[str, dict]]:
    """Helper to create a bundle with a single item and inventory result."""
    item = BundleItemSchema(
        product_id=product_id,
        name=name,
        brand="TestBrand",
        category="test_category",
        quantity=quantity,
        unit_price=unit_price,
        is_substituted=False,
        original_product_id=None,
        eta_minutes=30,
        eta_label="In 30 min",
        warehouse="WH-A",
    )
    bundle = BundleSchema(
        bundle_type="classic",
        bundle_name="Test Bundle",
        intent_type="general",
        items=[item],
        total_price=unit_price * quantity,
    )
    inventory = {product_id: {"available": available, "warehouse": "WH-A"}}
    return bundle, inventory


def _make_mock_db(sub_rows: list) -> AsyncMock:
    """Helper to create a mock database session with substitution rows."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sub_rows
    mock_db.execute = AsyncMock(return_value=mock_result)
    return mock_db


def _make_mock_substitution(
    original_id: str,
    replacement_id: str,
    confidence: float,
) -> MagicMock:
    """Helper to create a mock Substitution object."""
    sub = MagicMock()
    sub.original_product_id = original_id
    sub.replacement_product_id = replacement_id
    sub.confidence = confidence
    return sub


# --- Basic Functionality Tests ---


@pytest.mark.asyncio
async def test_no_oos_items_unchanged():
    """If all items are available, bundles are returned unchanged."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=True)
    
    result = await engine.apply([bundle], inventory, _make_mock_db([]))
    
    assert len(result) == 1
    assert len(result[0].items) == 1
    assert result[0].items[0].is_substituted is False
    assert result[0].items[0].product_id == "prod-001"
    assert result[0].items[0].original_product_id is None


@pytest.mark.asyncio
async def test_high_confidence_sub_auto_replaces():
    """OOS item with confidence >= 0.85 substitution is auto-replaced."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=False)

    sub = _make_mock_substitution("prod-001", "prod-002", 0.90)

    result = await engine.apply([bundle], inventory, _make_mock_db([sub]))
    
    item = result[0].items[0]
    assert item.is_substituted is True
    assert item.product_id == "prod-002"  # Replaced
    assert item.original_product_id == "prod-001"


@pytest.mark.asyncio
async def test_low_confidence_sub_flags_only():
    """OOS item with confidence < 0.85 substitution is flagged but NOT replaced."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=False)

    sub = _make_mock_substitution("prod-001", "prod-002", 0.70)

    result = await engine.apply([bundle], inventory, _make_mock_db([sub]))
    
    item = result[0].items[0]
    assert item.is_substituted is True
    assert item.product_id == "prod-001"  # NOT replaced
    assert item.original_product_id is None  # Not set for low confidence


@pytest.mark.asyncio
async def test_no_substitution_found_item_unchanged():
    """OOS item with no substitution row: left as is."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=False)
    
    result = await engine.apply([bundle], inventory, _make_mock_db([]))
    
    item = result[0].items[0]
    assert item.product_id == "prod-001"
    assert item.is_substituted is False


@pytest.mark.asyncio
async def test_best_substitution_chosen_when_multiple_exist():
    """When multiple substitution rows exist, the one with highest confidence wins."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=False)

    sub_low = _make_mock_substitution("prod-001", "prod-002", 0.60)
    sub_high = _make_mock_substitution("prod-001", "prod-003", 0.92)
    sub_mid = _make_mock_substitution("prod-001", "prod-004", 0.75)

    result = await engine.apply([bundle], inventory, _make_mock_db([sub_low, sub_high, sub_mid]))
    
    # Should choose sub_high (0.92 confidence)
    assert result[0].items[0].product_id == "prod-003"
    assert result[0].items[0].is_substituted is True


# --- Confidence Threshold Tests ---


@pytest.mark.asyncio
async def test_confidence_exactly_at_threshold_auto_replaces():
    """Confidence exactly at 0.85 should trigger auto-replacement."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=False)

    sub = _make_mock_substitution("prod-001", "prod-002", CONFIDENCE_AUTO_REPLACE_THRESHOLD)

    result = await engine.apply([bundle], inventory, _make_mock_db([sub]))
    
    item = result[0].items[0]
    assert item.product_id == "prod-002"  # Should replace
    assert item.is_substituted is True


@pytest.mark.asyncio
async def test_confidence_just_below_threshold_flags_only():
    """Confidence just below 0.85 should flag but not replace."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=False)

    sub = _make_mock_substitution("prod-001", "prod-002", 0.849)

    result = await engine.apply([bundle], inventory, _make_mock_db([sub]))
    
    item = result[0].items[0]
    assert item.product_id == "prod-001"  # Should NOT replace
    assert item.is_substituted is True


# --- Multiple Items Tests ---


@pytest.mark.asyncio
async def test_multiple_items_mixed_availability():
    """Bundle with mixed available/OOS items is processed correctly."""
    engine = SubstitutionEngine()
    
    # Create bundle with 3 items
    items = [
        BundleItemSchema(
            product_id="prod-001", name="Item 1", brand="B1", category="c1",
            quantity=1, unit_price=100.0, is_substituted=False,
            eta_minutes=30, eta_label="30 min", warehouse="WH-A",
        ),
        BundleItemSchema(
            product_id="prod-002", name="Item 2", brand="B2", category="c2",
            quantity=2, unit_price=50.0, is_substituted=False,
            eta_minutes=30, eta_label="30 min", warehouse="WH-A",
        ),
        BundleItemSchema(
            product_id="prod-003", name="Item 3", brand="B3", category="c3",
            quantity=1, unit_price=75.0, is_substituted=False,
            eta_minutes=30, eta_label="30 min", warehouse="WH-A",
        ),
    ]
    
    bundle = BundleSchema(
        bundle_type="classic", bundle_name="Test", intent_type="general",
        items=items, total_price=225.0,
    )
    
    # prod-001: available, prod-002: OOS with sub, prod-003: OOS no sub
    inventory = {
        "prod-001": {"available": True, "warehouse": "WH-A"},
        "prod-002": {"available": False, "warehouse": "WH-B"},
        "prod-003": {"available": False, "warehouse": "WH-C"},
    }
    
    sub = _make_mock_substitution("prod-002", "prod-004", 0.90)
    
    result = await engine.apply([bundle], inventory, _make_mock_db([sub]))
    
    # Check results
    assert len(result[0].items) == 3
    
    # Item 1: unchanged (available)
    assert result[0].items[0].product_id == "prod-001"
    assert result[0].items[0].is_substituted is False
    
    # Item 2: replaced (OOS with high confidence sub)
    assert result[0].items[1].product_id == "prod-004"
    assert result[0].items[1].is_substituted is True
    
    # Item 3: unchanged (OOS but no sub)
    assert result[0].items[2].product_id == "prod-003"
    assert result[0].items[2].is_substituted is False


# --- Multiple Bundles Tests ---


@pytest.mark.asyncio
async def test_multiple_bundles_processed_independently():
    """Multiple bundles are processed independently."""
    engine = SubstitutionEngine()
    
    bundle1, inv1 = _make_bundle_with_item("prod-001", available=False)
    bundle2, inv2 = _make_bundle_with_item("prod-002", available=False)
    
    inventory = {**inv1, **inv2}
    
    sub1 = _make_mock_substitution("prod-001", "prod-003", 0.90)
    sub2 = _make_mock_substitution("prod-002", "prod-004", 0.70)
    
    result = await engine.apply([bundle1, bundle2], inventory, _make_mock_db([sub1, sub2]))
    
    assert len(result) == 2
    
    # Bundle 1: high confidence replacement
    assert result[0].items[0].product_id == "prod-003"
    assert result[0].items[0].is_substituted is True
    
    # Bundle 2: low confidence flag only
    assert result[1].items[0].product_id == "prod-002"
    assert result[1].items[0].is_substituted is True


# --- Edge Cases ---


@pytest.mark.asyncio
async def test_empty_bundles_list():
    """Empty bundles list returns empty list."""
    engine = SubstitutionEngine()
    result = await engine.apply([], {}, _make_mock_db([]))
    assert result == []


@pytest.mark.asyncio
async def test_bundle_with_no_items():
    """Bundle with empty items list is handled gracefully."""
    engine = SubstitutionEngine()
    
    bundle = BundleSchema(
        bundle_type="classic", bundle_name="Empty", intent_type="general",
        items=[], total_price=0.0,
    )
    
    result = await engine.apply([bundle], {}, _make_mock_db([]))
    
    assert len(result) == 1
    assert len(result[0].items) == 0


@pytest.mark.asyncio
async def test_inventory_results_missing_product():
    """If inventory_results doesn't have a product, treat as available."""
    engine = SubstitutionEngine()
    bundle, _ = _make_bundle_with_item("prod-001", available=True)
    
    # Empty inventory (product not in results)
    result = await engine.apply([bundle], {}, _make_mock_db([]))
    
    # Should treat as available (not OOS)
    assert result[0].items[0].product_id == "prod-001"
    assert result[0].items[0].is_substituted is False


# --- Price Recalculation Tests ---


@pytest.mark.asyncio
async def test_total_price_recalculated_after_substitution():
    """Bundle total_price is recalculated after substitutions."""
    engine = SubstitutionEngine()
    
    # Create bundle with items at different prices
    items = [
        BundleItemSchema(
            product_id="prod-001", name="Item 1", brand="B1", category="c1",
            quantity=2, unit_price=100.0, is_substituted=False,
            eta_minutes=30, eta_label="30 min", warehouse="WH-A",
        ),
        BundleItemSchema(
            product_id="prod-002", name="Item 2", brand="B2", category="c2",
            quantity=1, unit_price=50.0, is_substituted=False,
            eta_minutes=30, eta_label="30 min", warehouse="WH-A",
        ),
    ]
    
    bundle = BundleSchema(
        bundle_type="classic", bundle_name="Test", intent_type="general",
        items=items, total_price=250.0,  # 2*100 + 1*50
    )
    
    inventory = {
        "prod-001": {"available": True, "warehouse": "WH-A"},
        "prod-002": {"available": False, "warehouse": "WH-B"},
    }
    
    # No substitution provided - total should still be recalculated
    result = await engine.apply([bundle], inventory, _make_mock_db([]))
    
    # Total should be recalculated: 2*100 + 1*50 = 250
    assert result[0].total_price == 250.0


# --- Substitution Row Format Tests ---


@pytest.mark.asyncio
async def test_handles_substitution_with_all_fields():
    """Handles substitution rows with all expected fields."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=False)

    sub = _make_mock_substitution("prod-001", "prod-002", 0.95)
    
    result = await engine.apply([bundle], inventory, _make_mock_db([sub]))
    
    assert result[0].items[0].product_id == "prod-002"
    assert result[0].items[0].is_substituted is True


# --- Database Query Tests ---


@pytest.mark.asyncio
async def test_db_query_only_for_oos_products():
    """Database query is only made when there are OOS products."""
    engine = SubstitutionEngine()
    bundle, inventory = _make_bundle_with_item("prod-001", available=True)
    
    mock_db = _make_mock_db([])
    result = await engine.apply([bundle], inventory, mock_db)
    
    # DB should NOT be queried (no OOS items)
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_db_query_batches_all_oos_products():
    """Database query includes all OOS product IDs in a single batch."""
    engine = SubstitutionEngine()
    
    # Create bundle with multiple OOS items
    items = [
        BundleItemSchema(
            product_id=f"prod-{i:03d}", name=f"Item {i}", brand="B", category="c",
            quantity=1, unit_price=100.0, is_substituted=False,
            eta_minutes=30, eta_label="30 min", warehouse="WH-A",
        )
        for i in range(1, 4)
    ]
    
    bundle = BundleSchema(
        bundle_type="classic", bundle_name="Test", intent_type="general",
        items=items, total_price=300.0,
    )
    
    inventory = {
        "prod-001": {"available": False, "warehouse": "WH-A"},
        "prod-002": {"available": False, "warehouse": "WH-B"},
        "prod-003": {"available": True, "warehouse": "WH-C"},
    }
    
    mock_db = _make_mock_db([])
    await engine.apply([bundle], inventory, mock_db)
    
    # DB should be queried exactly once
    assert mock_db.execute.call_count == 1


# --- Integration Tests ---


@pytest.mark.asyncio
async def test_real_world_scenario():
    """Test a realistic scenario with multiple bundles and substitutions."""
    engine = SubstitutionEngine()
    
    # Create 3 bundles: budget, classic, premium
    bundles = []
    for bundle_type in ["budget", "classic", "premium"]:
        items = [
            BundleItemSchema(
                product_id=f"{bundle_type}-001", name=f"{bundle_type} Item 1",
                brand="Brand A", category="category1",
                quantity=1, unit_price=50.0, is_substituted=False,
                eta_minutes=30, eta_label="30 min", warehouse="WH-A",
            ),
            BundleItemSchema(
                product_id=f"{bundle_type}-002", name=f"{bundle_type} Item 2",
                brand="Brand B", category="category2",
                quantity=2, unit_price=75.0, is_substituted=False,
                eta_minutes=45, eta_label="45 min", warehouse="WH-B",
            ),
        ]
        bundles.append(BundleSchema(
            bundle_type=bundle_type,
            bundle_name=f"{bundle_type.title()} Bundle",
            intent_type="meal_preparation",
            items=items,
            total_price=200.0,
        ))
    
    # Some items are OOS
    inventory = {
        "budget-001": {"available": False, "warehouse": "WH-A"},  # OOS with high conf sub
        "budget-002": {"available": True, "warehouse": "WH-B"},
        "classic-001": {"available": True, "warehouse": "WH-A"},
        "classic-002": {"available": False, "warehouse": "WH-B"},  # OOS with low conf sub
        "premium-001": {"available": False, "warehouse": "WH-A"},  # OOS no sub
        "premium-002": {"available": True, "warehouse": "WH-B"},
    }
    
    # Substitutions
    subs = [
        _make_mock_substitution("budget-001", "budget-001-alt", 0.92),
        _make_mock_substitution("classic-002", "classic-002-alt", 0.65),
    ]
    
    result = await engine.apply(bundles, inventory, _make_mock_db(subs))
    
    # Verify results
    assert len(result) == 3
    
    # Budget bundle: item 1 replaced, item 2 unchanged
    assert result[0].items[0].product_id == "budget-001-alt"
    assert result[0].items[0].is_substituted is True
    assert result[0].items[1].product_id == "budget-002"
    assert result[0].items[1].is_substituted is False
    
    # Classic bundle: item 1 unchanged, item 2 flagged
    assert result[1].items[0].product_id == "classic-001"
    assert result[1].items[0].is_substituted is False
    assert result[1].items[1].product_id == "classic-002"  # Not replaced (low confidence)
    assert result[1].items[1].is_substituted is True
    
    # Premium bundle: item 1 unchanged (no sub), item 2 unchanged
    assert result[2].items[0].product_id == "premium-001"
    assert result[2].items[0].is_substituted is False
    assert result[2].items[1].product_id == "premium-002"
    assert result[2].items[1].is_substituted is False
