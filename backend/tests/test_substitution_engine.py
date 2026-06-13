"""
Test suite for SubstitutionEngine (Phase 3).

Tests automatic product substitution for out-of-stock items.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.substitution_engine import SubstitutionEngine
from app.models.substitution import Substitution_Model
from app.schemas.bundle import BundleSchema, BundleItemSchema


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


def create_test_item(product_id, warehouse="", **kwargs):
    """Helper to create test bundle items."""
    defaults = {
        "name": f"Product {product_id}",
        "brand": "TestBrand",
        "category": "test_cat",
        "quantity": 1,
        "unit_price": 10.0,
        "eta_minutes": 30,
        "eta_label": "In 30 min"
    }
    defaults.update(kwargs)
    return BundleItemSchema(
        product_id=product_id,
        warehouse=warehouse,
        **defaults
    )


def create_test_bundle(items):
    """Helper to create test bundles."""
    total_price = sum(item.unit_price * item.quantity for item in items)
    return BundleSchema(
        bundle_type="classic",
        bundle_name="Test Bundle",
        intent_type="test_intent",
        items=items,
        total_price=total_price,
        final_score=0.0
    )


@pytest.mark.asyncio
async def test_apply_no_oos_items(mock_db):
    """SubstitutionEngine does nothing when all items in stock."""
    # All items have warehouse (in stock)
    items = [
        create_test_item("P1", warehouse="WH-A"),
        create_test_item("P2", warehouse="WH-B"),
    ]
    bundles = [create_test_bundle(items)]
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    # No DB queries should be made
    mock_db.execute.assert_not_called()
    
    # Items unchanged
    assert not result[0].items[0].is_substituted
    assert not result[0].items[1].is_substituted


@pytest.mark.asyncio
async def test_apply_with_oos_and_substitution(mock_db):
    """SubstitutionEngine replaces OOS items with available substitutes."""
    # Item P1 is OOS (no warehouse)
    items = [
        create_test_item("P1", warehouse=""),  # OOS
        create_test_item("P2", warehouse="WH-A"),  # In stock
    ]
    bundles = [create_test_bundle(items)]
    
    # Mock substitution: P1 -> P1-SUB
    mock_sub = Substitution_Model(
        id=uuid.uuid4(),
        original_product_id="P1",
        replacement_product_id="P1-SUB",
        reason="Similar product"
    )
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_sub]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    # First item should be substituted
    assert result[0].items[0].is_substituted is True
    assert result[0].items[0].original_product_id == "P1"
    assert result[0].items[0].product_id == "P1-SUB"
    
    # Second item unchanged
    assert result[0].items[1].is_substituted is False
    assert result[0].items[1].product_id == "P2"


@pytest.mark.asyncio
async def test_apply_oos_without_substitution(mock_db):
    """SubstitutionEngine keeps OOS items when no substitution available."""
    # Item P1 is OOS with no substitution
    items = [
        create_test_item("P1", warehouse=""),  # OOS, no sub
    ]
    bundles = [create_test_bundle(items)]
    
    # Mock: No substitutions found
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    # Item remains but not substituted
    assert len(result[0].items) == 1
    assert result[0].items[0].is_substituted is False
    assert result[0].items[0].product_id == "P1"


@pytest.mark.asyncio
async def test_apply_multiple_oos_items(mock_db):
    """SubstitutionEngine handles multiple OOS items in same bundle."""
    items = [
        create_test_item("P1", warehouse=""),  # OOS
        create_test_item("P2", warehouse=""),  # OOS
        create_test_item("P3", warehouse="WH-A"),  # In stock
    ]
    bundles = [create_test_bundle(items)]
    
    # Mock substitutions for both OOS items
    mock_subs = [
        Substitution_Model(
            id=uuid.uuid4(),
            original_product_id="P1",
            replacement_product_id="P1-SUB",
            reason="Alt 1"
        ),
        Substitution_Model(
            id=uuid.uuid4(),
            original_product_id="P2",
            replacement_product_id="P2-SUB",
            reason="Alt 2"
        ),
    ]
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = mock_subs
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    # Both OOS items substituted
    assert result[0].items[0].is_substituted is True
    assert result[0].items[0].product_id == "P1-SUB"
    assert result[0].items[1].is_substituted is True
    assert result[0].items[1].product_id == "P2-SUB"
    
    # Third item unchanged
    assert result[0].items[2].is_substituted is False


@pytest.mark.asyncio
async def test_apply_across_multiple_bundles(mock_db):
    """SubstitutionEngine applies substitutions across all bundles."""
    # Two bundles with same OOS product
    items1 = [create_test_item("P1", warehouse="")]
    items2 = [create_test_item("P1", warehouse="")]
    bundles = [create_test_bundle(items1), create_test_bundle(items2)]
    
    # Mock substitution
    mock_sub = Substitution_Model(
        id=uuid.uuid4(),
        original_product_id="P1",
        replacement_product_id="P1-SUB",
        reason="Alt"
    )
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_sub]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    # Both bundles updated
    assert result[0].items[0].product_id == "P1-SUB"
    assert result[1].items[0].product_id == "P1-SUB"


@pytest.mark.asyncio
async def test_apply_preserves_item_metadata(mock_db):
    """SubstitutionEngine preserves item metadata during substitution."""
    items = [
        create_test_item(
            "P1",
            warehouse="",
            name="Original Item",
            brand="OrigBrand",
            category="orig_cat",
            quantity=2,
            unit_price=15.99
        )
    ]
    bundles = [create_test_bundle(items)]
    
    # Mock substitution
    mock_sub = Substitution_Model(
        id=uuid.uuid4(),
        original_product_id="P1",
        replacement_product_id="P1-SUB",
        reason="Alt"
    )
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_sub]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    item = result[0].items[0]
    # Metadata preserved (Phase 3 - will be updated from catalog in Phase 4)
    assert item.name == "Original Item"
    assert item.brand == "OrigBrand"
    assert item.quantity == 2
    assert item.unit_price == 15.99


@pytest.mark.asyncio
async def test_apply_empty_bundles_list(mock_db):
    """SubstitutionEngine handles empty bundles list."""
    result = await SubstitutionEngine.apply([], mock_db)
    
    assert result == []
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_apply_bundles_with_no_items(mock_db):
    """SubstitutionEngine handles bundles with no items."""
    empty_bundle = BundleSchema(
        bundle_type="classic",
        bundle_name="Empty",
        intent_type="test",
        items=[],
        total_price=0.0,
        final_score=0.0
    )
    
    result = await SubstitutionEngine.apply([empty_bundle], mock_db)
    
    assert len(result) == 1
    assert len(result[0].items) == 0


@pytest.mark.asyncio
async def test_apply_no_confidence_threshold(mock_db):
    """SubstitutionEngine auto-replaces ALL found substitutions (no confidence check)."""
    # This test documents Phase 0 adaptation: NO confidence field
    items = [create_test_item("P1", warehouse="")]
    bundles = [create_test_bundle(items)]
    
    # Mock substitution WITHOUT confidence field (as per model)
    mock_sub = Substitution_Model(
        id=uuid.uuid4(),
        original_product_id="P1",
        replacement_product_id="P1-SUB",
        reason="Low confidence substitute"  # Even "low confidence" gets applied
    )
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_sub]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    # Substitution applied regardless of "confidence" (field doesn't exist)
    assert result[0].items[0].is_substituted is True
    assert result[0].items[0].product_id == "P1-SUB"


@pytest.mark.asyncio
async def test_apply_partial_substitutions(mock_db):
    """SubstitutionEngine handles mix of found and missing substitutions."""
    # Three OOS items: P1 has sub, P2 has sub, P3 has no sub
    items = [
        create_test_item("P1", warehouse=""),
        create_test_item("P2", warehouse=""),
        create_test_item("P3", warehouse=""),  # No substitution available
    ]
    bundles = [create_test_bundle(items)]
    
    # Mock only 2 substitutions (P3 has none)
    mock_subs = [
        Substitution_Model(
            id=uuid.uuid4(),
            original_product_id="P1",
            replacement_product_id="P1-SUB",
            reason="Alt"
        ),
        Substitution_Model(
            id=uuid.uuid4(),
            original_product_id="P2",
            replacement_product_id="P2-SUB",
            reason="Alt"
        ),
    ]
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = mock_subs
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Apply substitutions
    result = await SubstitutionEngine.apply(bundles, mock_db)
    
    # First two substituted
    assert result[0].items[0].is_substituted is True
    assert result[0].items[0].product_id == "P1-SUB"
    assert result[0].items[1].is_substituted is True
    assert result[0].items[1].product_id == "P2-SUB"
    
    # Third remains OOS (not substituted, but kept in bundle)
    assert result[0].items[2].is_substituted is False
    assert result[0].items[2].product_id == "P3"
    assert result[0].items[2].warehouse == ""  # Still OOS
