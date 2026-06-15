"""
Integration test suite for Bundle Router (Phase 4).

Tests the complete 12-step bundle generation pipeline end-to-end.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.routers.bundles import get_bundles
from app.models.intent import Intent_Model
from app.schemas.bundle import BundleListResponse
from app.exceptions import AppException


@pytest.fixture
def mock_db():
    """Mock database session."""
    mock = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def test_intent():
    """Create test intent."""
    return Intent_Model(
        id=uuid.uuid4(),
        user_id="test-user-123",
        session_id="sess-123",
        raw_text="I need pasta and sauce",
        intent_type="meal_preparation",
        confidence=0.85
    )


@pytest.mark.asyncio
async def test_get_bundles_intent_not_found(mock_db):
    """GET /v1/bundles/{intent_id} returns 404 when intent doesn't exist."""
    # Mock DB query returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    intent_id = uuid.uuid4()
    
    # Should raise AppException (converted to 404 by global handler)
    with pytest.raises(Exception) as exc_info:
        await get_bundles(intent_id, "test-user", mock_db)
    
    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_bundles_wrong_user(mock_db, test_intent):
    """GET /v1/bundles/{intent_id} returns 403 when intent belongs to different user."""
    # Mock DB returning intent for different user
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_intent
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Request from different user - should raise HTTPException
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_bundles(test_intent.id, "different-user", mock_db)
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
@patch('app.routers.bundles.cache_get')
@patch('app.routers.bundles.PersonalizationService')
@patch('app.routers.bundles.BundleGenerator')
@patch('app.routers.bundles.InventoryAdapter')
@patch('app.routers.bundles.ETAAdapter')
@patch('app.routers.bundles.SubstitutionEngine')
@patch('app.routers.bundles.RankingEngine')
@patch('app.routers.bundles.cache_set')
@patch('app.routers.bundles.emit')
async def test_get_bundles_full_pipeline(
    mock_emit,
    mock_cache_set,
    mock_ranking,
    mock_substitution,
    mock_eta,
    mock_inventory,
    mock_generator,
    mock_personalization,
    mock_cache_get,
    mock_db,
    test_intent
):
    """GET /v1/bundles/{intent_id} executes full 12-step pipeline."""
    # Step 1: Mock DB query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_intent
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    
    # Step 2: Mock cache miss
    mock_cache_get.return_value = None
    
    # Step 3: Mock personalization
    from app.services.personalization_service import PersonalizationSignals
    mock_signals = PersonalizationSignals(preferred_brands=["Barilla"])
    mock_personalization.get_signals = AsyncMock(return_value=mock_signals)
    
    # Step 4: Mock bundle generation
    from app.schemas.bundle import BundleSchema, BundleItemSchema
    mock_bundles = [
        BundleSchema(
            bundle_type="budget",
            bundle_name="Meal Preparation — Budget",
            intent_type="meal_preparation",
            items=[
                BundleItemSchema(
                    product_id="P1",
                    name="Pasta",
                    brand="Barilla",
                    category="pasta",
                    quantity=1,
                    unit_price=3.99,
                    eta_minutes=0,
                    eta_label="",
                    warehouse=""
                )
            ],
            total_price=3.99
        )
    ]
    mock_generator.generate.return_value = mock_bundles
    
    # Step 5: Mock inventory
    mock_inventory.check_batch = AsyncMock(return_value={
        "P1": {"available": True, "warehouse": "WH-A"}
    })
    
    # Step 6: Mock ETA
    mock_eta.get_batch = AsyncMock(return_value={
        "P1": {"eta_minutes": 30, "eta_label": "In 30 min"}
    })
    
    # Step 7: Mock substitution
    mock_substitution.apply = AsyncMock(return_value=mock_bundles)
    
    # Step 8: Mock ranking
    ranked_bundles = mock_bundles.copy()
    ranked_bundles[0].final_score = 0.85
    mock_ranking.rank.return_value = ranked_bundles
    
    # Step 9: DB persistence mocked by db.commit()
    
    # Step 10: Mock cache set
    mock_cache_set.return_value = None
    
    # Step 11: Mock event emission
    mock_emit.return_value = None
    
    # Execute
    result = await get_bundles(test_intent.id, test_intent.user_id, mock_db)
    
    # Verify result
    assert isinstance(result, BundleListResponse)
    assert result.intent_id == str(test_intent.id)
    assert len(result.options) == 1
    assert result.recommended == result.options[0]
    assert result.cache_hit is False
    
    # Verify all steps called
    mock_personalization.get_signals.assert_called_once()
    mock_generator.generate.assert_called_once()
    mock_inventory.check_batch.assert_called_once()
    mock_eta.get_batch.assert_called_once()
    mock_substitution.apply.assert_called_once()
    mock_ranking.rank.assert_called_once()
    mock_emit.assert_called_once()


@pytest.mark.asyncio
@patch('app.routers.bundles.cache_get')
@patch('app.routers.bundles.PersonalizationService')
@patch('app.routers.bundles.BundleGenerator')
@patch('app.routers.bundles.InventoryAdapter')
@patch('app.routers.bundles.ETAAdapter')
@patch('app.routers.bundles.SubstitutionEngine')
@patch('app.routers.bundles.RankingEngine')
@patch('app.routers.bundles.cache_set')
@patch('app.routers.bundles.emit')
async def test_get_bundles_uses_enriched_bundle_context(
    mock_emit,
    mock_cache_set,
    mock_ranking,
    mock_substitution,
    mock_eta,
    mock_inventory,
    mock_generator,
    mock_personalization,
    mock_cache_get,
    mock_db,
    test_intent,
):
    """GET /v1/bundles/{intent_id} should prefer enriched bundle_context when present."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_intent
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()

    mock_cache_get.side_effect = [
        {
            "intent_id": str(test_intent.id),
            "intent_type": "add_to_cart",
            "shopping_theme": None,
            "resolved_category": "dairy_and_bakery",
            "confirmed_entities": [
                {
                    "raw": "milk",
                    "canonical": "milk",
                    "brand": "amul",
                    "quantity": 5,
                    "unit": "items",
                }
            ],
            "constraints": {
                "quantity": 5,
                "budget": None,
                "brand": "amul",
                "diet": None,
            },
            "semantic_query": "amul milk breakfast groceries",
            "category_query": "dairy bakery breakfast groceries",
            "product_query_hints": ["milk", "amul"],
        },
        None,
    ]

    from app.services.personalization_service import PersonalizationSignals
    mock_personalization.get_signals = AsyncMock(return_value=PersonalizationSignals())

    from app.schemas.bundle import BundleSchema, BundleItemSchema
    mock_bundles = [
        BundleSchema(
            bundle_type="budget",
            bundle_name="Dairy and Bakery — Budget",
            intent_type="dairy_and_bakery",
            items=[
                BundleItemSchema(
                    product_id="P1",
                    name="Milk",
                    brand="Amul",
                    category="dairy",
                    quantity=1,
                    unit_price=45.0,
                    eta_minutes=0,
                    eta_label="",
                    warehouse="",
                )
            ],
            total_price=45.0,
        )
    ]
    mock_generator.generate.return_value = mock_bundles
    mock_inventory.check_batch = AsyncMock(return_value={"P1": {"warehouse": "WH-A"}})
    mock_eta.get_batch = AsyncMock(return_value={"P1": {"eta_minutes": 30, "eta_label": "In 30 min"}})
    mock_substitution.apply = AsyncMock(return_value=mock_bundles)
    mock_ranking.rank.return_value = mock_bundles
    mock_cache_set.return_value = None
    mock_emit.return_value = None

    result = await get_bundles(test_intent.id, test_intent.user_id, mock_db)

    assert isinstance(result, BundleListResponse)
    mock_generator.generate.assert_called_once()
    assert mock_generator.generate.call_args.args[0] == "dairy_and_bakery"
    mock_inventory.check_batch.assert_called_once()
    mock_emit.assert_called_once()


@pytest.mark.asyncio
@patch('app.routers.bundles.cache_get')
async def test_get_bundles_cache_hit(mock_cache_get, mock_db, test_intent):
    """GET /v1/bundles/{intent_id} returns cached data when available."""
    # Mock DB query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_intent
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Mock cache hit
    cached_response = {
        "intent_id": str(test_intent.id),
        "recommended": {
            "bundle_id": str(uuid.uuid4()),
            "bundle_type": "classic",
            "bundle_name": "Meal Preparation — Classic",
            "intent_type": "meal_preparation",
            "items": [],
            "total_price": 25.00,
            "final_score": 0.90
        },
        "options": [],
        "cache_hit": False  # Will be overridden
    }
    mock_cache_get.return_value = cached_response
    
    # Execute
    result = await get_bundles(test_intent.id, test_intent.user_id, mock_db)
    
    # Verify cache hit
    assert result.cache_hit is True
    assert result.intent_id == str(test_intent.id)


@pytest.mark.asyncio
@patch('app.routers.bundles.cache_get')
@patch('app.routers.bundles.PersonalizationService')
@patch('app.routers.bundles.BundleGenerator')
@patch('app.routers.bundles.InventoryAdapter')
@patch('app.routers.bundles.ETAAdapter')
@patch('app.routers.bundles.SubstitutionEngine')
@patch('app.routers.bundles.RankingEngine')
@patch('app.routers.bundles.cache_set')
@patch('app.routers.bundles.emit')
async def test_get_bundles_personalization_error_handling(
    mock_emit,
    mock_cache_set,
    mock_ranking,
    mock_substitution,
    mock_eta,
    mock_inventory,
    mock_generator,
    mock_personalization,
    mock_cache_get,
    mock_db,
    test_intent
):
    """GET /v1/bundles/{intent_id} continues with empty signals on personalization error."""
    # Mock DB query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_intent
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Mock cache miss
    mock_cache_get.return_value = None
    
    # Mock personalization failure
    mock_personalization.get_signals = AsyncMock(side_effect=Exception("DB error"))
    
    from app.schemas.bundle import BundleSchema, BundleItemSchema
    mock_bundles = [
        BundleSchema(
            bundle_type="budget",
            bundle_name="Meal Preparation — Budget",
            intent_type="meal_preparation",
            items=[
                BundleItemSchema(
                    product_id="P1",
                    name="Pasta",
                    brand="Barilla",
                    category="pasta",
                    quantity=1,
                    unit_price=3.99,
                    eta_minutes=0,
                    eta_label="",
                    warehouse="",
                )
            ],
            total_price=3.99,
        )
    ]
    mock_generator.generate.return_value = mock_bundles
    mock_inventory.check_batch = AsyncMock(return_value={"P1": {"warehouse": "WH-A"}})
    mock_eta.get_batch = AsyncMock(return_value={"P1": {"eta_minutes": 30, "eta_label": "In 30 min"}})
    mock_substitution.apply = AsyncMock(return_value=mock_bundles)
    mock_ranking.rank.return_value = mock_bundles
    mock_cache_set.return_value = None
    mock_emit.return_value = None

    result = await get_bundles(test_intent.id, test_intent.user_id, mock_db)

    assert result is not None
    mock_personalization.get_signals.assert_called_once()


@pytest.mark.asyncio
@patch('app.routers.bundles.cache_get')
@patch('app.routers.bundles.PersonalizationService')
@patch('app.routers.bundles.BundleGenerator')
async def test_get_bundles_generation_error(
    mock_generator,
    mock_personalization,
    mock_cache_get,
    mock_db,
    test_intent
):
    """GET /v1/bundles/{intent_id} returns 500 on bundle generation failure."""
    # Mock DB query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_intent
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Mock cache miss
    mock_cache_get.return_value = None
    
    # Mock personalization
    from app.services.personalization_service import PersonalizationSignals
    mock_personalization.get_signals = AsyncMock(return_value=PersonalizationSignals())
    
    # Mock generation failure
    mock_generator.generate.side_effect = Exception("Generation failed")
    
    # Should raise HTTPException 500
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_bundles(test_intent.id, test_intent.user_id, mock_db)
    
    assert exc_info.value.status_code == 500
