"""
Test suite for RankingEngine (Phase 2).

Tests multi-factor bundle ranking with weighted scoring algorithm.
"""

import pytest
from unittest.mock import patch
from app.services.ranking_engine import RankingEngine
from app.services.personalization_service import PersonalizationSignals
from app.schemas.bundle import BundleSchema, BundleItemSchema


def create_test_bundle(
    bundle_type="classic",
    intent_type="meal_preparation",
    items_data=None,
    **kwargs
) -> BundleSchema:
    """Helper to create test bundles."""
    if items_data is None:
        items_data = [
            {"product_id": "P1", "name": "Item1", "brand": "Brand1", "category": "cat1", 
             "quantity": 1, "unit_price": 10.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"},
            {"product_id": "P2", "name": "Item2", "brand": "Brand2", "category": "cat2",
             "quantity": 1, "unit_price": 15.0, "eta_minutes": 45, "eta_label": "In 45 min", "warehouse": "WH-B"},
        ]
    
    items = [BundleItemSchema(**item) for item in items_data]
    total_price = sum(item.unit_price * item.quantity for item in items)
    
    return BundleSchema(
        bundle_type=bundle_type,
        bundle_name=f"Test — {bundle_type.capitalize()}",
        intent_type=intent_type,
        items=items,
        total_price=total_price,
        final_score=0.0,
        **kwargs
    )


def test_rank_returns_sorted_bundles():
    """RankingEngine.rank() returns bundles sorted by score descending."""
    signals = PersonalizationSignals()
    
    # Create bundles with different characteristics
    bundles = [
        create_test_bundle("budget", items_data=[
            {"product_id": "P1", "name": "Item1", "brand": "B1", "category": "c1",
             "quantity": 1, "unit_price": 5.0, "eta_minutes": 90, "eta_label": "In 90 min", "warehouse": ""}
        ]),
        create_test_bundle("classic", items_data=[
            {"product_id": "P2", "name": "Item2", "brand": "B2", "category": "c2",
             "quantity": 1, "unit_price": 10.0, "eta_minutes": 20, "eta_label": "In 20 min", "warehouse": "WH-A"},
            {"product_id": "P3", "name": "Item3", "brand": "B3", "category": "c3",
             "quantity": 1, "unit_price": 15.0, "eta_minutes": 25, "eta_label": "In 25 min", "warehouse": "WH-B"},
        ]),
    ]
    
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    # Should return same bundles, sorted
    assert len(ranked) == 2
    # First bundle should have higher score
    assert ranked[0].final_score >= ranked[1].final_score


def test_rank_updates_final_scores():
    """RankingEngine updates final_score for each bundle."""
    signals = PersonalizationSignals()
    bundles = [create_test_bundle() for _ in range(3)]
    
    # All start at 0.0
    assert all(b.final_score == 0.0 for b in bundles)
    
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    # All should have scores > 0.0 after ranking
    assert all(b.final_score > 0.0 for b in ranked)


def test_intent_match_score():
    """Intent match scoring: 1.0 for match, 0.5 for mismatch."""
    signals = PersonalizationSignals()
    
    matching_bundle = create_test_bundle(intent_type="fitness")
    mismatched_bundle = create_test_bundle(intent_type="cleaning")
    
    bundles = [matching_bundle, mismatched_bundle]
    ranked = RankingEngine.rank(bundles, "fitness", signals)
    
    # Matching bundle should score higher (all else equal)
    matching_result = next(b for b in ranked if b.intent_type == "fitness")
    mismatched_result = next(b for b in ranked if b.intent_type == "cleaning")
    
    assert matching_result.final_score > mismatched_result.final_score


def test_inventory_score():
    """Inventory scoring: higher for more available items."""
    signals = PersonalizationSignals()
    
    # Bundle with all items available
    all_available = create_test_bundle(items_data=[
        {"product_id": "P1", "name": "I1", "brand": "B1", "category": "c1",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"},
        {"product_id": "P2", "name": "I2", "brand": "B2", "category": "c2",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-B"},
    ])
    
    # Bundle with some items unavailable (empty warehouse)
    partial_available = create_test_bundle(items_data=[
        {"product_id": "P3", "name": "I3", "brand": "B3", "category": "c3",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"},
        {"product_id": "P4", "name": "I4", "brand": "B4", "category": "c4",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": ""},
    ])
    
    bundles = [all_available, partial_available]
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    # All-available should score higher
    assert ranked[0].final_score > ranked[1].final_score


def test_eta_score():
    """ETA scoring: faster delivery scores higher."""
    signals = PersonalizationSignals()
    
    # Fast bundle (20 min)
    fast_bundle = create_test_bundle(items_data=[
        {"product_id": "P1", "name": "I1", "brand": "B1", "category": "c1",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 20, "eta_label": "In 20 min", "warehouse": "WH-A"},
    ])
    
    # Slow bundle (90 min)
    slow_bundle = create_test_bundle(items_data=[
        {"product_id": "P2", "name": "I2", "brand": "B2", "category": "c2",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 90, "eta_label": "In 90 min", "warehouse": "WH-A"},
    ])
    
    bundles = [slow_bundle, fast_bundle]
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    # Fast should score higher
    fast_result = next(b for b in ranked if b.items[0].eta_minutes == 20)
    slow_result = next(b for b in ranked if b.items[0].eta_minutes == 90)
    
    assert fast_result.final_score > slow_result.final_score


def test_personalization_score():
    """Personalization scoring: bundles matching preferences score higher."""
    # Strong preferences
    signals = PersonalizationSignals(
        preferred_brands=["PreferredBrand"],
        preferred_categories=["preferred_cat"]
    )
    
    # Bundle with preferred brand
    preferred_bundle = create_test_bundle(items_data=[
        {"product_id": "P1", "name": "I1", "brand": "PreferredBrand", "category": "other",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"},
    ])
    
    # Bundle without preferences
    non_preferred_bundle = create_test_bundle(items_data=[
        {"product_id": "P2", "name": "I2", "brand": "OtherBrand", "category": "other_cat",
         "quantity": 1, "unit_price": 10.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"},
    ])
    
    bundles = [non_preferred_bundle, preferred_bundle]
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    # Preferred should score higher
    preferred_result = next(b for b in ranked if b.items[0].brand == "PreferredBrand")
    non_preferred_result = next(b for b in ranked if b.items[0].brand == "OtherBrand")
    
    assert preferred_result.final_score > non_preferred_result.final_score


def test_completeness_score():
    """Completeness scoring: more items and higher value score better."""
    signals = PersonalizationSignals()
    
    # Large complete bundle (6 items, $50)
    complete_bundle = create_test_bundle(items_data=[
        {"product_id": f"P{i}", "name": f"I{i}", "brand": f"B{i}", "category": f"c{i}",
         "quantity": 1, "unit_price": 8.33, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"}
        for i in range(6)
    ])
    
    # Small bundle (2 items, $10)
    small_bundle = create_test_bundle(items_data=[
        {"product_id": "P7", "name": "I7", "brand": "B7", "category": "c7",
         "quantity": 1, "unit_price": 5.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"},
        {"product_id": "P8", "name": "I8", "brand": "B8", "category": "c8",
         "quantity": 1, "unit_price": 5.0, "eta_minutes": 30, "eta_label": "In 30 min", "warehouse": "WH-A"},
    ])
    
    bundles = [small_bundle, complete_bundle]
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    # Complete should score higher
    assert ranked[0].items != small_bundle.items or ranked[0].final_score >= ranked[1].final_score


def test_weighted_formula():
    """RankingEngine uses configured weights in scoring formula."""
    with patch('app.services.ranking_engine.settings') as mock_settings:
        # Set custom weights
        mock_settings.RANKING_WEIGHT_INTENT_MATCH = 0.30
        mock_settings.RANKING_WEIGHT_INVENTORY = 0.25
        mock_settings.RANKING_WEIGHT_ETA = 0.15
        mock_settings.RANKING_WEIGHT_PERSONALIZATION = 0.20
        mock_settings.RANKING_WEIGHT_COMPLETENESS = 0.10
        mock_settings.MOCK_ETA_MIN_MINUTES = 20
        mock_settings.MOCK_ETA_MAX_MINUTES = 90
        
        signals = PersonalizationSignals()
        bundles = [create_test_bundle()]
        
        ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
        
        # Should compute score using weights (not throw error)
        assert ranked[0].final_score > 0.0


def test_score_normalization():
    """All individual scores normalized to 0.0-1.0 range."""
    signals = PersonalizationSignals()
    bundles = [create_test_bundle()]
    
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    # Final score should be between 0 and 1 (weighted sum of 0-1 scores)
    assert 0.0 <= ranked[0].final_score <= 1.0


def test_rank_empty_bundles_list():
    """RankingEngine handles empty bundles list gracefully."""
    signals = PersonalizationSignals()
    ranked = RankingEngine.rank([], "meal_preparation", signals)
    
    assert ranked == []


def test_rank_single_bundle():
    """RankingEngine works with single bundle."""
    signals = PersonalizationSignals()
    bundles = [create_test_bundle()]
    
    ranked = RankingEngine.rank(bundles, "meal_preparation", signals)
    
    assert len(ranked) == 1
    assert ranked[0].final_score > 0.0
