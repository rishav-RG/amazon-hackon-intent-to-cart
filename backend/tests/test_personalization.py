"""
Tests for PersonalizationService.
Tests user preference reading and signal extraction.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.personalization_service import PersonalizationService, PersonalizationSignals


@pytest.mark.asyncio
async def test_get_signals_no_preference_returns_empty():
    """If user has no UserPreference row, return empty signals."""
    service = PersonalizationService()
    mock_db = AsyncMock()

    # Simulate no row found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    signals = await service.get_signals("user-unknown", mock_db)
    assert signals.preferred_brands == []
    assert signals.preferred_categories == []


@pytest.mark.asyncio
async def test_get_signals_returns_sorted_by_affinity():
    """Brands with higher affinity weight appear first."""
    service = PersonalizationService()
    mock_db = AsyncMock()

    mock_pref = MagicMock()
    mock_pref.brand_affinity = {"Amul": 0.9, "Barilla": 0.4, "Heinz": 0.7}
    mock_pref.category_affinity = {"dairy": 0.8, "pasta": 0.5}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)

    signals = await service.get_signals("user-1", mock_db)
    
    # Brands sorted by affinity descending
    assert signals.preferred_brands[0] == "Amul"    # 0.9
    assert signals.preferred_brands[1] == "Heinz"   # 0.7
    assert signals.preferred_brands[2] == "Barilla" # 0.4
    
    # Categories sorted by affinity descending
    assert signals.preferred_categories[0] == "dairy"  # 0.8
    assert signals.preferred_categories[1] == "pasta"  # 0.5


@pytest.mark.asyncio
async def test_get_signals_handles_null_affinity():
    """Handles None values in brand/category affinity gracefully."""
    service = PersonalizationService()
    mock_db = AsyncMock()

    mock_pref = MagicMock()
    mock_pref.brand_affinity = None
    mock_pref.category_affinity = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)

    signals = await service.get_signals("user-1", mock_db)
    assert signals.preferred_brands == []
    assert signals.preferred_categories == []


@pytest.mark.asyncio
async def test_get_signals_handles_empty_dicts():
    """Handles empty dictionaries in affinity fields."""
    service = PersonalizationService()
    mock_db = AsyncMock()

    mock_pref = MagicMock()
    mock_pref.brand_affinity = {}
    mock_pref.category_affinity = {}

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)

    signals = await service.get_signals("user-1", mock_db)
    assert signals.preferred_brands == []
    assert signals.preferred_categories == []


@pytest.mark.asyncio
async def test_personalization_signals_dataclass():
    """PersonalizationSignals dataclass works correctly."""
    # Default initialization
    signals1 = PersonalizationSignals()
    assert signals1.preferred_brands == []
    assert signals1.preferred_categories == []
    
    # With values
    signals2 = PersonalizationSignals(
        preferred_brands=["Amul", "Barilla"],
        preferred_categories=["dairy", "pasta"]
    )
    assert len(signals2.preferred_brands) == 2
    assert len(signals2.preferred_categories) == 2
