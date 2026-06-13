"""
Tests for RankingEngine.
Tests weighted scoring and bundle ranking.
"""
import pytest
from app.services.ranking_engine import RankingEngine
from app.services.bundle_generator import BundleGenerator
from app.services.personalization_service import PersonalizationSignals
from app.schemas.bundle import BundleSchema, BundleItemSchema


def _make_simple_bundle(bundle_type: str, price: float, product_id: str = "test-001") -> BundleSchema:
    """Helper to create a simple test bundle."""
    return BundleSchema(
        bundle_type=bundle_type,
        bundle_name=f"Test {bundle_type}",
        intent_type="meal_preparation",
        items=[
            BundleItemSchema(
                product_id=product_id,
                name="Test Product",
                brand="Barilla",
                category="pasta",
                quantity=1,
                unit_price=price,
                is_substituted=False,
                eta_minutes=30,
                eta_label="In 30 min",
                warehouse="WH-A",
            )
        ],
        total_price=price,
    )


def test_rank_returns_all_3_bundles():
    """Rank should return all input bundles."""
    engine = RankingEngine()
    bundles = [
        _make_simple_bundle("classic", 100),
        _make_simple_bundle("budget", 50),
        _make_simple_bundle("premium", 200)
    ]
    inventory = {"test-001": {"available": True, "warehouse": "WH-A"}}
    eta = {"test-001": {"eta_minutes": 30, "eta_label": "In 30 min"}}
    
    ranked = engine.rank(bundles, "meal_preparation", inventory, eta, PersonalizationSignals())
    assert len(ranked) == 3


def test_rank_sorted_descending():
    """Ranked bundles should be sorted by score descending."""
    engine = RankingEngine()
    bundles = [
        _make_simple_bundle("classic", 100),
        _make_simple_bundle("budget", 50),
        _make_simple_bundle("premium", 200)
    ]
    inventory = {"test-001": {"available": True, "warehouse": "WH-A"}}
    eta = {"test-001": {"eta_minutes": 30, "eta_label": "In 30 min"}}
    
    ranked = engine.rank(bundles, "meal_preparation", inventory, eta, PersonalizationSignals())
    scores = [b.final_score for b in ranked]
    assert scores == sorted(scores, reverse=True), "Scores should be descending"


def test_rank_scores_between_0_and_1():
    """All final scores should be in [0, 1] range."""
    engine = RankingEngine()
    bundles = [
        _make_simple_bundle("classic", 100),
        _make_simple_bundle("budget", 50),
        _make_simple_bundle("premium", 200)
    ]
    inventory = {"test-001": {"available": True, "warehouse": "WH-A"}}
    eta = {"test-001": {"eta_minutes": 30, "eta_label": "In 30 min"}}
    
    ranked = engine.rank(bundles, "meal_preparation", inventory, eta, PersonalizationSignals())
    for b in ranked:
        assert 0.0 <= b.final_score <= 1.0, f"Score {b.final_score} out of range"


def test_rank_oos_bundle_scores_lower():
    """A bundle with OOS items should rank lower than one with all available."""
    engine = RankingEngine()
    
    good = _make_simple_bundle("classic", 100, "prod-available")
    bad = _make_simple_bundle("budget", 100, "prod-oos")

    inventory = {
        "prod-available": {"available": True, "warehouse": "WH-A"},
        "prod-oos": {"available": False, "warehouse": "WH-B"},
    }
    eta = {
        "prod-available": {"eta_minutes": 30, "eta_label": "In 30 min"},
        "prod-oos": {"eta_minutes": 30, "eta_label": "In 30 min"},
    }
    
    ranked = engine.rank([good, bad], "meal_preparation", inventory, eta, PersonalizationSignals())
    
    # Bundle with available products should rank higher
    assert ranked[0].items[0].product_id == "prod-available"
    assert ranked[0].final_score > ranked[1].final_score


def test_ranking_formula_float_precision():
    """Scores should use consistent float precision."""
    engine = RankingEngine()
    bundle = _make_simple_bundle("classic", 100)
    inventory = {"test-001": {"available": True, "warehouse": "WH-A"}}
    eta = {"test-001": {"eta_minutes": 30, "eta_label": "In 30 min"}}
    
    ranked = engine.rank([bundle], "meal_preparation", inventory, eta, PersonalizationSignals())
    
    # Score should be a clean float
    assert isinstance(ranked[0].final_score, float)
    # Should have reasonable precision (6 decimal places from round())
    assert len(str(ranked[0].final_score).split('.')[-1]) <= 6


def test_personalization_boosts_score():
    """Bundles with preferred brands/categories should score higher."""
    engine = RankingEngine()
    
    # Bundle with preferred brand
    preferred = BundleSchema(
        bundle_type="classic",
        bundle_name="Preferred",
        intent_type="meal_preparation",
        items=[
            BundleItemSchema(
                product_id="p1",
                name="Amul Butter",
                brand="Amul",  # Will be in preferred_brands
                category="dairy",
                quantity=1,
                unit_price=100,
                is_substituted=False,
                eta_minutes=30,
                eta_label="In 30 min",
                warehouse="WH-A",
            )
        ],
        total_price=100,
    )
    
    # Bundle without preferred brand
    not_preferred = BundleSchema(
        bundle_type="budget",
        bundle_name="Not Preferred",
        intent_type="meal_preparation",
        items=[
            BundleItemSchema(
                product_id="p2",
                name="Generic Product",
                brand="Generic",  # Not in preferred_brands
                category="other",
                quantity=1,
                unit_price=100,
                is_substituted=False,
                eta_minutes=30,
                eta_label="In 30 min",
                warehouse="WH-A",
            )
        ],
        total_price=100,
    )
    
    inventory = {
        "p1": {"available": True, "warehouse": "WH-A"},
        "p2": {"available": True, "warehouse": "WH-A"},
    }
    eta = {
        "p1": {"eta_minutes": 30, "eta_label": "In 30 min"},
        "p2": {"eta_minutes": 30, "eta_label": "In 30 min"},
    }
    
    signals = PersonalizationSignals(
        preferred_brands=["Amul"],
        preferred_categories=["dairy"]
    )
    
    ranked = engine.rank([preferred, not_preferred], "meal_preparation", inventory, eta, signals)
    
    # Preferred bundle should rank higher
    assert ranked[0].items[0].brand == "Amul"
    assert ranked[0].final_score > ranked[1].final_score


def test_empty_bundle_scores_zero():
    """Bundle with no items should score 0."""
    engine = RankingEngine()
    
    empty_bundle = BundleSchema(
        bundle_type="classic",
        bundle_name="Empty",
        intent_type="meal_preparation",
        items=[],  # No items
        total_price=0,
    )
    
    ranked = engine.rank([empty_bundle], "meal_preparation", {}, {}, PersonalizationSignals())
    assert ranked[0].final_score == 0.0


def test_faster_eta_scores_higher():
    """Bundles with faster delivery should score higher."""
    engine = RankingEngine()
    
    fast = _make_simple_bundle("classic", 100, "prod-fast")
    slow = _make_simple_bundle("budget", 100, "prod-slow")
    
    inventory = {
        "prod-fast": {"available": True, "warehouse": "WH-A"},
        "prod-slow": {"available": True, "warehouse": "WH-A"},
    }
    eta = {
        "prod-fast": {"eta_minutes": 20, "eta_label": "In 20 min"},  # Faster
        "prod-slow": {"eta_minutes": 80, "eta_label": "In 80 min"},  # Slower
    }
    
    ranked = engine.rank([fast, slow], "meal_preparation", inventory, eta, PersonalizationSignals())
    
    # Faster delivery should rank higher (assuming all else equal)
    fast_bundle = next(b for b in ranked if b.items[0].product_id == "prod-fast")
    slow_bundle = next(b for b in ranked if b.items[0].product_id == "prod-slow")
    assert fast_bundle.final_score > slow_bundle.final_score


def test_ranking_with_real_bundles():
    """Test ranking with bundles from BundleGenerator."""
    gen = BundleGenerator()
    engine = RankingEngine()
    signals = PersonalizationSignals()
    
    bundles = gen.generate("fitness", [], signals)
    
    # Create mock inventory and ETA for all products
    all_product_ids = [item.product_id for b in bundles for item in b.items]
    inventory = {pid: {"available": True, "warehouse": "WH-A"} for pid in all_product_ids}
    eta = {pid: {"eta_minutes": 30, "eta_label": "In 30 min"} for pid in all_product_ids}
    
    ranked = engine.rank(bundles, "fitness", inventory, eta, signals)
    
    # Should have 3 ranked bundles
    assert len(ranked) == 3
    # All should have scores
    assert all(b.final_score > 0 for b in ranked)
    # Should be sorted
    assert ranked[0].final_score >= ranked[1].final_score >= ranked[2].final_score
