"""
Test suite for PersonalizationService (Phase 2).

Tests extraction of user preference signals from UserPreference model.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.personalization_service import PersonalizationService, PersonalizationSignals
from app.models.user_preference import UserPreference_Model


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_get_signals_with_preferences(mock_db):
    """PersonalizationService returns signals when preferences exist."""
    user_id = "user-123"
    
    # Mock user preferences with high affinity values
    mock_pref = UserPreference_Model(
        id=uuid.uuid4(),
        user_id=user_id,
        brand_preferences={"Barilla": 0.9, "Amul": 0.7, "Dove": 0.4},  # Dove below threshold
        category_preferences={"pasta": 0.85, "dairy": 0.6, "snacks": 0.3},  # snacks below threshold
        reorder_affinity={"prod-001": 0.9}
    )
    
    # Mock DB query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Get signals
    signals = await PersonalizationService.get_signals(user_id, mock_db)
    
    # Verify correct extraction
    assert isinstance(signals, PersonalizationSignals)
    assert signals.preferred_brands == ["Barilla", "Amul"]  # Sorted by affinity, Dove excluded (< 0.5)
    assert signals.preferred_categories == ["pasta", "dairy"]  # Sorted by affinity, snacks excluded


@pytest.mark.asyncio
async def test_get_signals_no_preferences(mock_db):
    """PersonalizationService returns empty signals when no preferences found."""
    user_id = "user-456"
    
    # Mock DB query returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Get signals
    signals = await PersonalizationService.get_signals(user_id, mock_db)
    
    # Verify empty signals
    assert isinstance(signals, PersonalizationSignals)
    assert signals.preferred_brands == []
    assert signals.preferred_categories == []


@pytest.mark.asyncio
async def test_get_signals_empty_preferences(mock_db):
    """PersonalizationService handles empty preference dicts."""
    user_id = "user-789"
    
    # Mock user with empty preference dicts
    mock_pref = UserPreference_Model(
        id=uuid.uuid4(),
        user_id=user_id,
        brand_preferences={},
        category_preferences={},
        reorder_affinity={}
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Get signals
    signals = await PersonalizationService.get_signals(user_id, mock_db)
    
    # Verify empty lists
    assert signals.preferred_brands == []
    assert signals.preferred_categories == []


@pytest.mark.asyncio
async def test_get_signals_sorts_by_affinity(mock_db):
    """PersonalizationService sorts preferences by affinity score descending."""
    user_id = "user-sort"
    
    # Mock preferences with varying affinity (unsorted)
    mock_pref = UserPreference_Model(
        id=uuid.uuid4(),
        user_id=user_id,
        brand_preferences={"Brand_A": 0.6, "Brand_B": 0.9, "Brand_C": 0.75},
        category_preferences={"cat_x": 0.5, "cat_y": 0.95, "cat_z": 0.7},
        reorder_affinity={}
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Get signals
    signals = await PersonalizationService.get_signals(user_id, mock_db)
    
    # Verify sorting (highest affinity first)
    assert signals.preferred_brands == ["Brand_B", "Brand_C", "Brand_A"]  # 0.9, 0.75, 0.6
    assert signals.preferred_categories == ["cat_y", "cat_z", "cat_x"]  # 0.95, 0.7, 0.5


@pytest.mark.asyncio
async def test_get_signals_threshold_filtering(mock_db):
    """PersonalizationService filters out preferences below 0.5 threshold."""
    user_id = "user-threshold"
    
    # Mix of above and below threshold
    mock_pref = UserPreference_Model(
        id=uuid.uuid4(),
        user_id=user_id,
        brand_preferences={
            "High": 0.8,
            "Exact": 0.5,
            "Low": 0.49,
            "VeryLow": 0.1
        },
        category_preferences={
            "Good": 0.6,
            "Bad": 0.3
        },
        reorder_affinity={}
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Get signals
    signals = await PersonalizationService.get_signals(user_id, mock_db)
    
    # Only >= 0.5 included
    assert "High" in signals.preferred_brands
    assert "Exact" in signals.preferred_brands
    assert "Low" not in signals.preferred_brands
    assert "VeryLow" not in signals.preferred_brands
    assert "Good" in signals.preferred_categories
    assert "Bad" not in signals.preferred_categories


@pytest.mark.asyncio
async def test_get_signals_uses_correct_field_names(mock_db):
    """PersonalizationService uses correct UserPreference field names."""
    user_id = "user-fields"
    
    # Verify we're using brand_preferences NOT brand_affinity
    mock_pref = UserPreference_Model(
        id=uuid.uuid4(),
        user_id=user_id,
        brand_preferences={"TestBrand": 0.9},
        category_preferences={"TestCategory": 0.8},
        reorder_affinity={}
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_pref
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Should not raise AttributeError
    signals = await PersonalizationService.get_signals(user_id, mock_db)
    
    assert "TestBrand" in signals.preferred_brands
    assert "TestCategory" in signals.preferred_categories
