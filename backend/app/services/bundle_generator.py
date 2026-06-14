"""
BundleGenerator for Intent-to-Cart backend.

Generates three-tier bundles (budget, classic, premium) based on user intent
and personalization signals. Uses a 48-product mock catalog across 8 intent categories.
"""

from typing import Literal
from app.schemas.bundle import BundleSchema, BundleItemSchema
from app.services.personalization_service import PersonalizationSignals


# 48-product mock catalog across 8 intent types
MOCK_CATALOG = {
    "meal_preparation": [
        {"product_id": "MP-001", "name": "Organic Basmati Rice", "brand": "India Gate", "category": "grains", "price": 12.99, "unit": "1kg"},
        {"product_id": "MP-002", "name": "Whole Wheat Pasta", "brand": "Barilla", "category": "pasta", "price": 3.49, "unit": "500g"},
        {"product_id": "MP-003", "name": "Extra Virgin Olive Oil", "brand": "Bertolli", "category": "oils", "price": 8.99, "unit": "500ml"},
        {"product_id": "MP-004", "name": "Tomato Passata", "brand": "Mutti", "category": "sauces", "price": 2.99, "unit": "680g"},
        {"product_id": "MP-005", "name": "Fresh Basil", "brand": "Local Farm", "category": "herbs", "price": 1.99, "unit": "bunch"},
        {"product_id": "MP-006", "name": "Garlic Cloves", "brand": "Local Farm", "category": "vegetables", "price": 0.99, "unit": "100g"},
    ],
    "party_supplies": [
        {"product_id": "PS-001", "name": "Party Plates (50 pack)", "brand": "Glad", "category": "disposables", "price": 5.99, "unit": "pack"},
        {"product_id": "PS-002", "name": "Plastic Cups (100 pack)", "brand": "Solo", "category": "disposables", "price": 7.49, "unit": "pack"},
        {"product_id": "PS-003", "name": "Paper Napkins (200 pack)", "brand": "Bounty", "category": "disposables", "price": 4.99, "unit": "pack"},
        {"product_id": "PS-004", "name": "Potato Chips", "brand": "Lay's", "category": "snacks", "price": 3.99, "unit": "200g"},
        {"product_id": "PS-005", "name": "Soda (12 pack)", "brand": "Coca-Cola", "category": "beverages", "price": 8.99, "unit": "12x330ml"},
        {"product_id": "PS-006", "name": "Party Balloons (30 pack)", "brand": "PartyCity", "category": "decorations", "price": 4.49, "unit": "pack"},
    ],
    "cleaning": [
        {"product_id": "CL-001", "name": "All-Purpose Cleaner", "brand": "Mr. Clean", "category": "cleaners", "price": 4.99, "unit": "750ml"},
        {"product_id": "CL-002", "name": "Dish Soap", "brand": "Dawn", "category": "dish_care", "price": 3.49, "unit": "600ml"},
        {"product_id": "CL-003", "name": "Glass Cleaner", "brand": "Windex", "category": "cleaners", "price": 3.99, "unit": "750ml"},
        {"product_id": "CL-004", "name": "Paper Towels (6 rolls)", "brand": "Bounty", "category": "paper_products", "price": 12.99, "unit": "6 rolls"},
        {"product_id": "CL-005", "name": "Sponges (5 pack)", "brand": "Scotch-Brite", "category": "cleaning_tools", "price": 4.49, "unit": "5 pack"},
        {"product_id": "CL-006", "name": "Trash Bags (50 pack)", "brand": "Glad", "category": "bags", "price": 11.99, "unit": "50 pack"},
    ],
    "baby_care": [
        {"product_id": "BC-001", "name": "Baby Diapers Size 3 (84 pack)", "brand": "Pampers", "category": "diapers", "price": 34.99, "unit": "84 pack"},
        {"product_id": "BC-002", "name": "Baby Wipes (400 pack)", "brand": "Huggies", "category": "wipes", "price": 12.99, "unit": "400 pack"},
        {"product_id": "BC-003", "name": "Baby Shampoo", "brand": "Johnson's", "category": "bath", "price": 5.99, "unit": "400ml"},
        {"product_id": "BC-004", "name": "Baby Lotion", "brand": "Cetaphil", "category": "skincare", "price": 7.99, "unit": "400ml"},
        {"product_id": "BC-005", "name": "Baby Food Pouches (12 pack)", "brand": "Gerber", "category": "food", "price": 15.99, "unit": "12 pack"},
        {"product_id": "BC-006", "name": "Baby Formula", "brand": "Similac", "category": "formula", "price": 28.99, "unit": "850g"},
    ],
    "fitness": [
        {"product_id": "FT-001", "name": "Protein Powder (Vanilla)", "brand": "Optimum Nutrition", "category": "supplements", "price": 39.99, "unit": "2kg"},
        {"product_id": "FT-002", "name": "Energy Bars (12 pack)", "brand": "Clif Bar", "category": "snacks", "price": 18.99, "unit": "12 pack"},
        {"product_id": "FT-003", "name": "Sports Drink (8 pack)", "brand": "Gatorade", "category": "beverages", "price": 9.99, "unit": "8x500ml"},
        {"product_id": "FT-004", "name": "Greek Yogurt (4 pack)", "brand": "Chobani", "category": "dairy", "price": 5.99, "unit": "4x150g"},
        {"product_id": "FT-005", "name": "Almonds", "brand": "Blue Diamond", "category": "nuts", "price": 8.99, "unit": "400g"},
        {"product_id": "FT-006", "name": "Resistance Bands Set", "brand": "TheraBand", "category": "equipment", "price": 14.99, "unit": "set"},
    ],
    "pet_care": [
        {"product_id": "PC-001", "name": "Dog Food (10kg)", "brand": "Pedigree", "category": "food", "price": 42.99, "unit": "10kg"},
        {"product_id": "PC-002", "name": "Cat Food (5kg)", "brand": "Whiskas", "category": "food", "price": 21.99, "unit": "5kg"},
        {"product_id": "PC-003", "name": "Dog Treats", "brand": "Greenies", "category": "treats", "price": 9.99, "unit": "340g"},
        {"product_id": "PC-004", "name": "Cat Litter (10L)", "brand": "Tidy Cats", "category": "litter", "price": 14.99, "unit": "10L"},
        {"product_id": "PC-005", "name": "Pet Shampoo", "brand": "Burt's Bees", "category": "grooming", "price": 8.99, "unit": "500ml"},
        {"product_id": "PC-006", "name": "Chew Toys Set", "brand": "KONG", "category": "toys", "price": 12.99, "unit": "set"},
    ],
    "office_supplies": [
        {"product_id": "OS-001", "name": "Printer Paper (500 sheets)", "brand": "HP", "category": "paper", "price": 8.99, "unit": "500 sheets"},
        {"product_id": "OS-002", "name": "Ballpoint Pens (12 pack)", "brand": "BIC", "category": "pens", "price": 4.99, "unit": "12 pack"},
        {"product_id": "OS-003", "name": "Sticky Notes (6 pads)", "brand": "Post-it", "category": "notes", "price": 6.99, "unit": "6 pads"},
        {"product_id": "OS-004", "name": "Stapler + Staples", "brand": "Swingline", "category": "tools", "price": 9.99, "unit": "set"},
        {"product_id": "OS-005", "name": "File Folders (25 pack)", "brand": "Pendaflex", "category": "filing", "price": 11.99, "unit": "25 pack"},
        {"product_id": "OS-006", "name": "Desk Organizer", "brand": "SimpleHouseware", "category": "organization", "price": 14.99, "unit": "unit"},
    ],
    "general": [
        {"product_id": "GN-001", "name": "Toilet Paper (12 rolls)", "brand": "Charmin", "category": "paper_products", "price": 14.99, "unit": "12 rolls"},
        {"product_id": "GN-002", "name": "Hand Soap (3 pack)", "brand": "Dove", "category": "personal_care", "price": 7.99, "unit": "3x250ml"},
        {"product_id": "GN-003", "name": "Shampoo", "brand": "Pantene", "category": "hair_care", "price": 6.99, "unit": "400ml"},
        {"product_id": "GN-004", "name": "Toothpaste (2 pack)", "brand": "Colgate", "category": "oral_care", "price": 5.99, "unit": "2x150g"},
        {"product_id": "GN-005", "name": "Laundry Detergent", "brand": "Tide", "category": "laundry", "price": 18.99, "unit": "2L"},
        {"product_id": "GN-006", "name": "AA Batteries (12 pack)", "brand": "Duracell", "category": "batteries", "price": 12.99, "unit": "12 pack"},
    ],
}


class BundleGenerator:
    """
    Generates three-tier product bundles based on intent and personalization.
    
    Creates budget, classic, and premium bundles by selecting products from
    the mock catalog and applying personalization boosting.
    """
    
    @staticmethod
    def generate(
        intent_type: str,
        user_id: str,
        signals: PersonalizationSignals,
        products: list[dict] | None = None,
    ) -> list[BundleSchema]:
        """
        Generate three bundles (budget, classic, premium) for the given intent.
        
        Args:
            intent_type: The classified intent type (e.g., "meal_preparation").
            user_id: The user ID (for naming/tracking).
            signals: Personalization signals for product boosting.
            products: OPTIONAL retrieved products (from ProductRetriever). When
                provided, bundles are composed from these instead of MOCK_CATALOG.
                Each dict must contain: product_id, name, brand, category, price.
                When None, behavior is exactly the original MOCK_CATALOG path.
            
        Returns:
            List of 3 BundleSchema objects (budget, classic, premium).
            
        Algorithm:
            1. Get products: retrieved products if provided, else MOCK_CATALOG[intent_type]
            2. Boost/prioritize products matching user preferences
            3. Split into 3 tiers:
               - Budget: 3-4 cheapest items
               - Classic: 4-5 mid-range items (most complete)
               - Premium: 4-5 premium items (includes boosted brands)
            4. Set initial quantities (1 for most, 2-3 for consumables)
            
        Note:
            - Falls back to "general" intent if intent_type not in catalog
            - Returns bundles with final_score=0.0 (scoring happens in RankingEngine)
            - Bundle names include intent type (e.g., "Meal Preparation — Budget")
        """
        # Get products: prefer retrieved products, else MOCK_CATALOG (fallback general)
        if products:
            products = products
        else:
            products = MOCK_CATALOG.get(intent_type, MOCK_CATALOG["general"])
        
        # Apply personalization boosting
        boosted_products = BundleGenerator._apply_personalization_boost(
            products, signals
        )
        
        # Sort by price for tier splitting
        sorted_by_price = sorted(boosted_products, key=lambda p: p["price"])
        
        # Generate three tiers
        bundles = []
        
        # Budget bundle: 3-4 cheapest items
        budget_products = sorted_by_price[:4]
        bundles.append(BundleGenerator._create_bundle(
            "budget", intent_type, user_id, budget_products
        ))
        
        # Classic bundle: 4-5 mid-range items (most balanced)
        classic_products = sorted_by_price[1:6] if len(sorted_by_price) >= 6 else sorted_by_price[1:5]
        bundles.append(BundleGenerator._create_bundle(
            "classic", intent_type, user_id, classic_products
        ))
        
        # Premium bundle: 4-5 most expensive items + boosted brands
        premium_products = sorted_by_price[-4:]
        # Add boosted brand products if available
        for prod in boosted_products:
            if prod.get("_boosted") and prod not in premium_products:
                premium_products.insert(0, prod)
                if len(premium_products) > 5:
                    premium_products.pop()
                    break
        bundles.append(BundleGenerator._create_bundle(
            "premium", intent_type, user_id, premium_products
        ))
        
        return bundles
    
    @staticmethod
    def _apply_personalization_boost(
        products: list[dict],
        signals: PersonalizationSignals
    ) -> list[dict]:
        """
        Boost products matching user preferences.
        
        Marks products with preferred brands/categories with _boosted flag
        for use in premium bundle selection.
        """
        boosted = []
        for prod in products:
            prod_copy = prod.copy()
            if (prod["brand"] in signals.preferred_brands or 
                prod["category"] in signals.preferred_categories):
                prod_copy["_boosted"] = True
            boosted.append(prod_copy)
        return boosted
    
    @staticmethod
    def _create_bundle(
        bundle_type: Literal["budget", "classic", "premium"],
        intent_type: str,
        user_id: str,
        products: list[dict]
    ) -> BundleSchema:
        """
        Create a single bundle from selected products.
        
        Sets initial quantities and calculates total price.
        Returns bundle with final_score=0.0 (scoring in RankingEngine).
        """
        # Create bundle items with default quantities
        items = []
        total_price = 0.0
        
        for prod in products:
            # Default quantity (2-3 for consumables like food/cleaning, 1 for others)
            quantity = 1
            if prod["category"] in ["food", "snacks", "beverages", "cleaners", "dish_care"]:
                quantity = 2
            
            item = BundleItemSchema(
                product_id=prod["product_id"],
                name=prod["name"],
                brand=prod["brand"],
                category=prod["category"],
                quantity=quantity,
                unit_price=prod["price"],
                image_url=prod.get("image_url", ""),
                # Runtime fields set by adapters later
                eta_minutes=0,  # Will be set by ETAAdapter
                eta_label="",    # Will be set by ETAAdapter
                warehouse=""     # Will be set by InventoryAdapter
            )
            items.append(item)
            total_price += prod["price"] * quantity
        
        # Format bundle name
        intent_display = intent_type.replace("_", " ").title()
        type_display = bundle_type.capitalize()
        bundle_name = f"{intent_display} — {type_display}"
        
        return BundleSchema(
            bundle_type=bundle_type,
            bundle_name=bundle_name,
            intent_type=intent_type,
            items=items,
            total_price=round(total_price, 2),
            final_score=0.0  # Set by RankingEngine
        )
