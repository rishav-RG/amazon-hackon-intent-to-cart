"""
Bundle generator service - creates 3 product bundles from intent.
Developer B owns this file.
"""
from __future__ import annotations
from typing import Optional
from app.schemas.bundle import BundleSchema, BundleItemSchema
from app.services.personalization_service import PersonalizationSignals

# Mock product catalog (~48 products across 8 intent types)
# Structure: { intent_type: [ {product_id, name, brand, category, price, unit}, ... ] }
MOCK_CATALOG: dict[str, list[dict]] = {
    "meal_preparation": [
        # Budget tier
        {"product_id": "mp-001", "name": "Tata Salt 1kg",            "brand": "Tata",     "category": "spice",     "price": 24.0,  "unit": "pack"},
        {"product_id": "mp-002", "name": "Fresho Garlic 250g",       "brand": "Fresho",   "category": "vegetable", "price": 45.0,  "unit": "pack"},
        {"product_id": "mp-003", "name": "Amul Butter 100g",         "brand": "Amul",     "category": "dairy",     "price": 52.0,  "unit": "pack"},
        {"product_id": "mp-004", "name": "MTR Pasta 500g",           "brand": "MTR",      "category": "pasta",     "price": 60.0,  "unit": "pack"},
        # Classic tier
        {"product_id": "mp-005", "name": "Barilla Spaghetti 500g",   "brand": "Barilla",  "category": "pasta",     "price": 85.0,  "unit": "pack"},
        {"product_id": "mp-006", "name": "Kissan Ketchup 500g",      "brand": "Kissan",   "category": "sauce",     "price": 95.0,  "unit": "bottle"},
        # Premium tier
        {"product_id": "mp-007", "name": "Heinz Pasta Sauce 350g",   "brand": "Heinz",    "category": "sauce",     "price": 175.0, "unit": "jar"},
        {"product_id": "mp-008", "name": "Del Monte Olive Oil 500ml","brand": "Del Monte","category": "oil",       "price": 285.0, "unit": "bottle"},
    ],
    
    "party_supplies": [
        {"product_id": "ps-001", "name": "Kurkure Masala 100g",      "brand": "Kurkure",  "category": "snack",     "price": 20.0,  "unit": "pack"},
        {"product_id": "ps-002", "name": "Lay's Classic 78g",        "brand": "Lay's",    "category": "snack",     "price": 30.0,  "unit": "pack"},
        {"product_id": "ps-003", "name": "Bingo Mad Angles 72g",     "brand": "Bingo",    "category": "snack",     "price": 25.0,  "unit": "pack"},
        {"product_id": "ps-004", "name": "Pepsi 2L",                 "brand": "Pepsi",    "category": "beverage",  "price": 65.0,  "unit": "bottle"},
        {"product_id": "ps-005", "name": "Paper Plates 50pcs",       "brand": "Generic",  "category": "tableware", "price": 85.0,  "unit": "pack"},
        {"product_id": "ps-006", "name": "Solo Plastic Cups 50pcs",  "brand": "Solo",     "category": "tableware", "price": 145.0, "unit": "pack"},
        {"product_id": "ps-007", "name": "Pringles Original 110g",   "brand": "Pringles", "category": "snack",     "price": 120.0, "unit": "can"},
    ],
    
    "cleaning": [
        {"product_id": "cl-001", "name": "Scotch-Brite Scrubber",    "brand": "3M",       "category": "scrubber",  "price": 38.0,  "unit": "piece"},
        {"product_id": "cl-002", "name": "Colin Glass Cleaner 500ml","brand": "Colin",    "category": "glass",     "price": 62.0,  "unit": "bottle"},
        {"product_id": "cl-003", "name": "Vim Dish Wash Gel 500ml",  "brand": "Vim",      "category": "dishwash",  "price": 72.0,  "unit": "bottle"},
        {"product_id": "cl-004", "name": "Harpic Toilet Cleaner",    "brand": "Harpic",   "category": "bathroom",  "price": 89.0,  "unit": "bottle"},
        {"product_id": "cl-005", "name": "Domex Floor Cleaner 500ml","brand": "Domex",    "category": "floor",     "price": 95.0,  "unit": "bottle"},
        {"product_id": "cl-006", "name": "Lizol Floor Cleaner 500ml","brand": "Lizol",    "category": "floor",     "price": 145.0, "unit": "bottle"},
        {"product_id": "cl-007", "name": "Dettol Surface Cleaner",   "brand": "Dettol",   "category": "multi",     "price": 175.0, "unit": "bottle"},
    ],
    
    "baby_care": [
        {"product_id": "bc-001", "name": "Mamy Poko Pants M 20pcs",  "brand": "MamyPoko", "category": "diaper",    "price": 289.0, "unit": "pack"},
        {"product_id": "bc-002", "name": "Johnson's Baby Powder 100g","brand":"Johnson's", "category": "powder",    "price": 115.0, "unit": "bottle"},
        {"product_id": "bc-003", "name": "Pampers S/M Diapers 20pcs","brand": "Pampers",  "category": "diaper",    "price": 320.0, "unit": "pack"},
        {"product_id": "bc-004", "name": "Dettol Baby Wipes 72pcs",  "brand": "Dettol",   "category": "wipes",     "price": 190.0, "unit": "pack"},
        {"product_id": "bc-005", "name": "Chicco Baby Wash 200ml",   "brand": "Chicco",   "category": "wash",      "price": 235.0, "unit": "bottle"},
        {"product_id": "bc-006", "name": "Huggies Pants M 30pcs",    "brand": "Huggies",  "category": "diaper",    "price": 510.0, "unit": "pack"},
        {"product_id": "bc-007", "name": "Himalaya Baby Lotion 200ml","brand":"Himalaya", "category": "lotion",    "price": 165.0, "unit": "bottle"},
    ],
    
    "fitness": [
        {"product_id": "ft-001", "name": "Skipping Rope",            "brand": "Generic",  "category": "equipment", "price": 149.0, "unit": "piece"},
        {"product_id": "ft-002", "name": "Yoga Mat 6mm",             "brand": "Generic",  "category": "equipment", "price": 599.0, "unit": "piece"},
        {"product_id": "ft-003", "name": "Resistance Band Set",      "brand": "Generic",  "category": "equipment", "price": 349.0, "unit": "set"},
        {"product_id": "ft-004", "name": "Protein Shaker 600ml",     "brand": "Generic",  "category": "accessory", "price": 199.0, "unit": "piece"},
        {"product_id": "ft-005", "name": "Whey Protein 1kg",         "brand": "MuscleBlaze","category":"protein",   "price": 1499.0,"unit": "pack"},
        {"product_id": "ft-006", "name": "Creatine Monohydrate 250g","brand":"Optimum",   "category": "supplement","price": 999.0, "unit": "pack"},
        {"product_id": "ft-007", "name": "Gym Gloves",               "brand": "Nivia",    "category": "accessory", "price": 299.0, "unit": "pair"},
    ],
    
    "pet_care": [
        {"product_id": "pc-001", "name": "Drools Dog Food 1kg",      "brand": "Drools",   "category": "pet_food",  "price": 220.0, "unit": "pack"},
        {"product_id": "pc-002", "name": "Whiskas Cat Food 500g",    "brand": "Whiskas",  "category": "pet_food",  "price": 175.0, "unit": "pack"},
        {"product_id": "pc-003", "name": "Pedigree Dog Food 1kg",    "brand": "Pedigree", "category": "pet_food",  "price": 250.0, "unit": "pack"},
        {"product_id": "pc-004", "name": "Dog Shampoo 200ml",        "brand": "PetStar",  "category": "grooming",  "price": 190.0, "unit": "bottle"},
        {"product_id": "pc-005", "name": "Cat Litter 5kg",           "brand": "Meo",      "category": "hygiene",   "price": 385.0, "unit": "pack"},
        {"product_id": "pc-006", "name": "Royal Canin Adult Dog 3kg","brand": "RoyalCanin","category":"pet_food",  "price": 1850.0,"unit": "pack"},
    ],
    
    "office_supplies": [
        {"product_id": "os-001", "name": "Fevicol MR 200g",          "brand": "Fevicol",  "category": "adhesive",  "price": 45.0,  "unit": "bottle"},
        {"product_id": "os-002", "name": "Reynolds Pens 10pcs",      "brand": "Reynolds", "category": "stationery","price": 65.0,  "unit": "pack"},
        {"product_id": "os-003", "name": "Scotch Tape 24mm 2pcs",    "brand": "3M",       "category": "tape",      "price": 95.0,  "unit": "pack"},
        {"product_id": "os-004", "name": "Classmate Notebooks 6pcs", "brand": "Classmate","category": "stationery","price": 180.0, "unit": "set"},
        {"product_id": "os-005", "name": "Stapler + Pins",           "brand": "Kangaro",  "category": "stationery","price": 125.0, "unit": "set"},
        {"product_id": "os-006", "name": "Parker Pen",               "brand": "Parker",   "category": "stationery","price": 450.0, "unit": "piece"},
        {"product_id": "os-007", "name": "Post-it Notes 3x3 12pads", "brand": "3M",       "category": "stationery","price": 385.0, "unit": "pack"},
    ],
    
    "general": [
        {"product_id": "gn-001", "name": "Dettol Handwash 250ml",    "brand": "Dettol",   "category": "hygiene",   "price": 55.0,  "unit": "bottle"},
        {"product_id": "gn-002", "name": "Colgate Toothpaste 200g",  "brand": "Colgate",  "category": "oral_care", "price": 105.0, "unit": "tube"},
        {"product_id": "gn-003", "name": "Tissue Paper 200 pulls",   "brand": "Kleenex",  "category": "tissue",    "price": 120.0, "unit": "box"},
        {"product_id": "gn-004", "name": "Listerine Mouthwash 250ml","brand": "Listerine","category": "oral_care", "price": 165.0, "unit": "bottle"},
        {"product_id": "gn-005", "name": "Gillette Razor + 4 Blades","brand": "Gillette", "category": "grooming",  "price": 285.0, "unit": "set"},
    ],
}


class BundleGenerator:
    """
    Generates 3 product bundles (classic, budget, premium) for a given intent.
    Uses the mock catalog — no DB reads here.
    
    Personalization:
      Products whose brand is in preferred_brands get prioritized (moved to
      top of their price tier). Products whose category is in preferred_categories
      are also prioritized.
    """

    def generate(
        self,
        intent_type: str,
        clarifications: list[dict],
        signals: PersonalizationSignals,
    ) -> list[BundleSchema]:
        """
        Returns exactly 3 BundleSchema objects: classic, budget, premium.
        
        Items will not have eta/warehouse fields yet — those are filled by the
        router after InventoryAdapter and ETAAdapter calls.

        Args:
            intent_type: e.g. "meal_preparation"
            clarifications: list of { question, answer } dicts (optional)
            signals: PersonalizationSignals from PersonalizationService

        Returns:
            [classic_bundle, budget_bundle, premium_bundle]
            
        Notes:
            - Falls back to "general" catalog if intent_type not found
            - Each bundle gets top 3 products from its price tier
            - Personalization boosts preferred brands/categories to top
        """
        # Get products for this intent type, fallback to general
        candidates: list[dict] = MOCK_CATALOG.get(intent_type, MOCK_CATALOG["general"])

        # Apply personalization: sort preferred brands/categories to the top
        def personalization_score(product: dict) -> int:
            score = 0
            if product["brand"] in signals.preferred_brands:
                score += 2
            if product["category"] in signals.preferred_categories:
                score += 1
            return score

        candidates_sorted = sorted(
            candidates, key=personalization_score, reverse=True
        )

        # Split into 3 price tiers
        prices_sorted = sorted(candidates_sorted, key=lambda p: p["price"])
        third = max(1, len(prices_sorted) // 3)

        budget_pool    = prices_sorted[:third]
        classic_pool   = prices_sorted[third : third * 2]
        premium_pool   = prices_sorted[third * 2 :]

        # Ensure each pool has at least 1 item (fallback to full pool)
        budget_pool  = budget_pool  or candidates_sorted[:2]
        classic_pool = classic_pool or candidates_sorted[:3]
        premium_pool = premium_pool or candidates_sorted[-2:]

        # Take top 3 from each pool (personalization order preserved)
        def make_items(pool: list[dict]) -> list[BundleItemSchema]:
            return [
                BundleItemSchema(
                    product_id=p["product_id"],
                    name=p["name"],
                    brand=p["brand"],
                    category=p["category"],
                    quantity=1,
                    unit_price=p["price"],
                    is_substituted=False,
                    original_product_id=None,
                    eta_minutes=0,       # placeholder — filled by router
                    eta_label="",        # placeholder — filled by router
                    warehouse="",        # placeholder — filled by router
                )
                for p in pool[:3]
            ]

        classic_items = make_items(classic_pool)
        budget_items  = make_items(budget_pool)
        premium_items = make_items(premium_pool)

        return [
            BundleSchema(
                bundle_type="classic",
                bundle_name=f"{intent_type.replace('_', ' ').title()} — Classic",
                intent_type=intent_type,
                items=classic_items,
                total_price=sum(i.unit_price * i.quantity for i in classic_items),
            ),
            BundleSchema(
                bundle_type="budget",
                bundle_name=f"{intent_type.replace('_', ' ').title()} — Budget",
                intent_type=intent_type,
                items=budget_items,
                total_price=sum(i.unit_price * i.quantity for i in budget_items),
            ),
            BundleSchema(
                bundle_type="premium",
                bundle_name=f"{intent_type.replace('_', ' ').title()} — Premium",
                intent_type=intent_type,
                items=premium_items,
                total_price=sum(i.unit_price * i.quantity for i in premium_items),
            ),
        ]
