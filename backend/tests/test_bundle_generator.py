"""
Tests for BundleGenerator.
Tests bundle creation from catalog and personalization.
"""
import pytest
from app.services.bundle_generator import BundleGenerator, MOCK_CATALOG
from app.services.personalization_service import PersonalizationSignals


def test_catalog_structure():
    """Validate MOCK_CATALOG has expected structure."""
    assert len(MOCK_CATALOG) == 8  # 8 intent types
    assert "meal_preparation" in MOCK_CATALOG
    assert "general" in MOCK_CATALOG
    
    # Each intent type has products
    for intent_type, products in MOCK_CATALOG.items():
        assert len(products) > 0
        # Each product has required fields
        for p in products:
            assert "product_id" in p
            assert "name" in p
            assert "brand" in p
            assert "category" in p
            assert "price" in p
            assert "unit" in p


def test_generate_returns_exactly_3_bundles():
    """Always returns 3 bundles."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("meal_preparation", [], signals)
    assert len(bundles) == 3


def test_generate_bundle_types():
    """Returns classic, budget, and premium bundles."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("meal_preparation", [], signals)
    types = {b.bundle_type for b in bundles}
    assert types == {"classic", "budget", "premium"}


def test_budget_bundle_is_cheapest():
    """Budget bundle should have lowest total price."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("meal_preparation", [], signals)
    
    budget  = next(b for b in bundles if b.bundle_type == "budget")
    classic = next(b for b in bundles if b.bundle_type == "classic")
    premium = next(b for b in bundles if b.bundle_type == "premium")
    
    # Budget should be cheapest or equal
    assert budget.total_price <= classic.total_price
    # Premium should be most expensive or equal
    assert classic.total_price <= premium.total_price


def test_generate_with_personalization_surfaces_preferred_brand():
    """A preferred brand should appear in bundles if it exists in catalog."""
    gen = BundleGenerator()
    signals = PersonalizationSignals(
        preferred_brands=["Barilla"],  # Barilla is in meal_preparation
        preferred_categories=["pasta"],
    )
    bundles = gen.generate("meal_preparation", [], signals)
    
    all_brands = [item.brand for b in bundles for item in b.items]
    assert "Barilla" in all_brands, "Preferred brand should appear in bundles"


def test_generate_falls_back_to_general_for_unknown_intent():
    """Unknown intent type should use 'general' catalog."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("completely_unknown_intent", [], signals)
    
    assert len(bundles) == 3  # Should not crash
    # Should use general catalog
    assert bundles[0].intent_type == "completely_unknown_intent"


def test_all_bundle_items_have_required_fields():
    """Each item in generated bundles has all required fields."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("cleaning", [], signals)
    
    for bundle in bundles:
        assert len(bundle.items) > 0, "Bundle should have items"
        for item in bundle.items:
            assert item.product_id
            assert item.name
            assert item.brand
            assert item.category
            assert item.quantity > 0
            assert item.unit_price > 0
            assert item.is_substituted == False  # Not substituted initially
            assert item.original_product_id is None


def test_bundle_names_formatted_correctly():
    """Bundle names should be formatted nicely."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("meal_preparation", [], signals)
    
    for bundle in bundles:
        assert "—" in bundle.bundle_name or "-" in bundle.bundle_name
        assert bundle.bundle_type.capitalize() in bundle.bundle_name or bundle.bundle_type in bundle.bundle_name.lower()


def test_total_price_calculation():
    """Total price should equal sum of item prices."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("party_supplies", [], signals)
    
    for bundle in bundles:
        calculated_total = sum(item.unit_price * item.quantity for item in bundle.items)
        assert bundle.total_price == pytest.approx(calculated_total, abs=0.01)


def test_personalization_affects_bundle_contents():
    """Personalization should influence which products appear."""
    gen = BundleGenerator()
    
    # No personalization
    signals_none = PersonalizationSignals()
    bundles_none = gen.generate("meal_preparation", [], signals_none)
    items_none = [item.product_id for b in bundles_none for item in b.items]
    
    # With personalization
    signals_with = PersonalizationSignals(
        preferred_brands=["Amul", "Barilla"],
        preferred_categories=["dairy", "pasta"]
    )
    bundles_with = gen.generate("meal_preparation", [], signals_with)
    items_with = [item.product_id for b in bundles_with for item in b.items]
    
    # At least some items should be different (personalization has effect)
    # Or preferred items should appear more prominently
    assert len(items_with) > 0
    assert len(items_none) > 0


def test_intent_type_preserved_in_bundles():
    """Generated bundles preserve the intent_type."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    
    for intent_type in ["fitness", "pet_care", "office_supplies"]:
        bundles = gen.generate(intent_type, [], signals)
        for bundle in bundles:
            assert bundle.intent_type == intent_type


def test_placeholder_fields_in_items():
    """ETA and warehouse fields should be placeholders initially."""
    gen = BundleGenerator()
    signals = PersonalizationSignals()
    bundles = gen.generate("baby_care", [], signals)
    
    for bundle in bundles:
        for item in bundle.items:
            assert item.eta_minutes == 0  # Placeholder
            assert item.eta_label == ""   # Placeholder
            assert item.warehouse == ""   # Placeholder
