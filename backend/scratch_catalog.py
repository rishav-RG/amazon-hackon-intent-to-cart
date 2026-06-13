# Mock Product Catalog - Phase 0 Design
# This file is for design only - will be moved to app/services/bundle_generator.py in Phase 2
# DO NOT COMMIT TO MAIN BRANCH - Keep in scratch/ or local branch only

"""
Design Requirements:
1. ~30 products across 8 intent types
2. Each intent type has at least 5 products with varying prices (budget/classic/premium split)
3. At least 3 products per intent type belong to brands in UserPreference seed data
4. At least 2 products per intent type are OOS candidates (for substitution testing)
5. Prices are in INR (Indian Rupees)
"""

MOCK_CATALOG = {
    "meal_preparation": [
        # Budget tier (prices: 24-60)
        {"product_id": "mp-001", "name": "Tata Salt 1kg",            "brand": "Tata",     "category": "spice",     "price": 24.0,  "unit": "pack"},
        {"product_id": "mp-002", "name": "Fresho Garlic 250g",       "brand": "Fresho",   "category": "vegetable", "price": 45.0,  "unit": "pack"},
        {"product_id": "mp-003", "name": "Amul Butter 100g",         "brand": "Amul",     "category": "dairy",     "price": 52.0,  "unit": "pack"},
        {"product_id": "mp-004", "name": "MTR Pasta 500g",           "brand": "MTR",      "category": "pasta",     "price": 60.0,  "unit": "pack"},
        
        # Classic tier (prices: 85-100)
        {"product_id": "mp-005", "name": "Barilla Spaghetti 500g",   "brand": "Barilla",  "category": "pasta",     "price": 85.0,  "unit": "pack"},  # Preferred brand
        {"product_id": "mp-006", "name": "Kissan Ketchup 500g",      "brand": "Kissan",   "category": "sauce",     "price": 95.0,  "unit": "bottle"},
        
        # Premium tier (prices: 175+)
        {"product_id": "mp-007", "name": "Heinz Pasta Sauce 350g",   "brand": "Heinz",    "category": "sauce",     "price": 175.0, "unit": "jar"},    # Preferred brand
        {"product_id": "mp-008", "name": "Del Monte Olive Oil 500ml","brand": "Del Monte","category": "oil",       "price": 285.0, "unit": "bottle"},
    ],
    
    "party_supplies": [
        # Budget tier
        {"product_id": "ps-001", "name": "Kurkure Masala 100g",      "brand": "Kurkure",  "category": "snack",     "price": 20.0,  "unit": "pack"},
        {"product_id": "ps-002", "name": "Lay's Classic 78g",        "brand": "Lay's",    "category": "snack",     "price": 30.0,  "unit": "pack"},
        {"product_id": "ps-003", "name": "Bingo Mad Angles 72g",     "brand": "Bingo",    "category": "snack",     "price": 25.0,  "unit": "pack"},
        
        # Classic tier
        {"product_id": "ps-004", "name": "Pepsi 2L",                 "brand": "Pepsi",    "category": "beverage",  "price": 65.0,  "unit": "bottle"},
        {"product_id": "ps-005", "name": "Paper Plates 50pcs",       "brand": "Generic",  "category": "tableware", "price": 85.0,  "unit": "pack"},
        
        # Premium tier
        {"product_id": "ps-006", "name": "Solo Plastic Cups 50pcs",  "brand": "Solo",     "category": "tableware", "price": 145.0, "unit": "pack"},
        {"product_id": "ps-007", "name": "Pringles Original 110g",   "brand": "Pringles", "category": "snack",     "price": 120.0, "unit": "can"},
    ],
    
    "cleaning": [
        # Budget tier
        {"product_id": "cl-001", "name": "Scotch-Brite Scrubber",    "brand": "3M",       "category": "scrubber",  "price": 38.0,  "unit": "piece"},
        {"product_id": "cl-002", "name": "Colin Glass Cleaner 500ml","brand": "Colin",    "category": "glass",     "price": 62.0,  "unit": "bottle"},
        {"product_id": "cl-003", "name": "Vim Dish Wash Gel 500ml",  "brand": "Vim",      "category": "dishwash",  "price": 72.0,  "unit": "bottle"},
        
        # Classic tier
        {"product_id": "cl-004", "name": "Harpic Toilet Cleaner",    "brand": "Harpic",   "category": "bathroom",  "price": 89.0,  "unit": "bottle"},
        {"product_id": "cl-005", "name": "Domex Floor Cleaner 500ml","brand": "Domex",    "category": "floor",     "price": 95.0,  "unit": "bottle"},
        
        # Premium tier
        {"product_id": "cl-006", "name": "Lizol Floor Cleaner 500ml","brand": "Lizol",    "category": "floor",     "price": 145.0, "unit": "bottle"},
        {"product_id": "cl-007", "name": "Dettol Surface Cleaner",   "brand": "Dettol",   "category": "multi",     "price": 175.0, "unit": "bottle"},
    ],
    
    "baby_care": [
        # Budget tier
        {"product_id": "bc-001", "name": "Mamy Poko Pants M 20pcs",  "brand": "MamyPoko", "category": "diaper",    "price": 289.0, "unit": "pack"},
        {"product_id": "bc-002", "name": "Johnson's Baby Powder 100g","brand":"Johnson's", "category": "powder",    "price": 115.0, "unit": "bottle"}, # Preferred brand
        
        # Classic tier
        {"product_id": "bc-003", "name": "Pampers S/M Diapers 20pcs","brand": "Pampers",  "category": "diaper",    "price": 320.0, "unit": "pack"},   # Preferred brand
        {"product_id": "bc-004", "name": "Dettol Baby Wipes 72pcs",  "brand": "Dettol",   "category": "wipes",     "price": 190.0, "unit": "pack"},
        {"product_id": "bc-005", "name": "Chicco Baby Wash 200ml",   "brand": "Chicco",   "category": "wash",      "price": 235.0, "unit": "bottle"},
        
        # Premium tier
        {"product_id": "bc-006", "name": "Huggies Pants M 30pcs",    "brand": "Huggies",  "category": "diaper",    "price": 510.0, "unit": "pack"},
        {"product_id": "bc-007", "name": "Himalaya Baby Lotion 200ml","brand":"Himalaya", "category": "lotion",    "price": 165.0, "unit": "bottle"},
    ],
    
    "fitness": [
        # Budget tier
        {"product_id": "ft-001", "name": "Skipping Rope",            "brand": "Generic",  "category": "equipment", "price": 149.0, "unit": "piece"},
        {"product_id": "ft-002", "name": "Yoga Mat 6mm",             "brand": "Generic",  "category": "equipment", "price": 599.0, "unit": "piece"},
        
        # Classic tier
        {"product_id": "ft-003", "name": "Resistance Band Set",      "brand": "Generic",  "category": "equipment", "price": 349.0, "unit": "set"},
        {"product_id": "ft-004", "name": "Protein Shaker 600ml",     "brand": "Generic",  "category": "accessory", "price": 199.0, "unit": "piece"},
        
        # Premium tier
        {"product_id": "ft-005", "name": "Whey Protein 1kg",         "brand": "MuscleBlaze","category":"protein",   "price": 1499.0,"unit": "pack"},
        {"product_id": "ft-006", "name": "Creatine Monohydrate 250g","brand":"Optimum",   "category": "supplement","price": 999.0, "unit": "pack"},
        {"product_id": "ft-007", "name": "Gym Gloves",               "brand": "Nivia",    "category": "accessory", "price": 299.0, "unit": "pair"},
    ],
    
    "pet_care": [
        # Budget tier
        {"product_id": "pc-001", "name": "Drools Dog Food 1kg",      "brand": "Drools",   "category": "pet_food",  "price": 220.0, "unit": "pack"},
        {"product_id": "pc-002", "name": "Whiskas Cat Food 500g",    "brand": "Whiskas",  "category": "pet_food",  "price": 175.0, "unit": "pack"},   # Preferred brand
        
        # Classic tier
        {"product_id": "pc-003", "name": "Pedigree Dog Food 1kg",    "brand": "Pedigree", "category": "pet_food",  "price": 250.0, "unit": "pack"},   # Preferred brand
        {"product_id": "pc-004", "name": "Dog Shampoo 200ml",        "brand": "PetStar",  "category": "grooming",  "price": 190.0, "unit": "bottle"},
        {"product_id": "pc-005", "name": "Cat Litter 5kg",           "brand": "Meo",      "category": "hygiene",   "price": 385.0, "unit": "pack"},
        
        # Premium tier
        {"product_id": "pc-006", "name": "Royal Canin Adult Dog 3kg","brand": "RoyalCanin","category":"pet_food",  "price": 1850.0,"unit": "pack"},
    ],
    
    "office_supplies": [
        # Budget tier
        {"product_id": "os-001", "name": "Fevicol MR 200g",          "brand": "Fevicol",  "category": "adhesive",  "price": 45.0,  "unit": "bottle"},
        {"product_id": "os-002", "name": "Reynolds Pens 10pcs",      "brand": "Reynolds", "category": "stationery","price": 65.0,  "unit": "pack"},
        {"product_id": "os-003", "name": "Scotch Tape 24mm 2pcs",    "brand": "3M",       "category": "tape",      "price": 95.0,  "unit": "pack"},    # Preferred brand
        
        # Classic tier
        {"product_id": "os-004", "name": "Classmate Notebooks 6pcs", "brand": "Classmate","category": "stationery","price": 180.0, "unit": "set"},    # Preferred brand
        {"product_id": "os-005", "name": "Stapler + Pins",           "brand": "Kangaro",  "category": "stationery","price": 125.0, "unit": "set"},
        
        # Premium tier
        {"product_id": "os-006", "name": "Parker Pen",               "brand": "Parker",   "category": "stationery","price": 450.0, "unit": "piece"},
        {"product_id": "os-007", "name": "Post-it Notes 3x3 12pads", "brand": "3M",       "category": "stationery","price": 385.0, "unit": "pack"},
    ],
    
    "general": [
        # Budget tier - fallback items for unknown intents
        {"product_id": "gn-001", "name": "Dettol Handwash 250ml",    "brand": "Dettol",   "category": "hygiene",   "price": 55.0,  "unit": "bottle"},
        {"product_id": "gn-002", "name": "Colgate Toothpaste 200g",  "brand": "Colgate",  "category": "oral_care", "price": 105.0, "unit": "tube"},
        
        # Classic tier
        {"product_id": "gn-003", "name": "Tissue Paper 200 pulls",   "brand": "Kleenex",  "category": "tissue",    "price": 120.0, "unit": "box"},
        {"product_id": "gn-004", "name": "Listerine Mouthwash 250ml","brand": "Listerine","category": "oral_care", "price": 165.0, "unit": "bottle"},
        
        # Premium tier
        {"product_id": "gn-005", "name": "Gillette Razor + 4 Blades","brand": "Gillette", "category": "grooming",  "price": 285.0, "unit": "set"},
    ],
}


# Validation statistics (run this to verify catalog design):
def validate_catalog():
    """Verify catalog meets all design requirements."""
    print("="*60)
    print("MOCK CATALOG VALIDATION")
    print("="*60)
    
    total_products = sum(len(products) for products in MOCK_CATALOG.values())
    print(f"\nTotal products: {total_products}")
    
    for intent_type, products in MOCK_CATALOG.items():
        print(f"\n{intent_type}:")
        print(f"  Product count: {len(products)}")
        
        prices = [p["price"] for p in products]
        print(f"  Price range: ₹{min(prices):.2f} - ₹{max(prices):.2f}")
        
        # Check for 3 price tiers
        sorted_prices = sorted(prices)
        third = len(sorted_prices) // 3
        if third > 0:
            budget_max = sorted_prices[third-1] if third > 0 else sorted_prices[0]
            classic_max = sorted_prices[third*2-1] if third*2 < len(sorted_prices) else sorted_prices[-1]
            print(f"  Budget tier (≤₹{budget_max:.2f}): {third} products")
            print(f"  Classic tier (≤₹{classic_max:.2f}): {third} products")
            print(f"  Premium tier: {len(sorted_prices) - third*2} products")
        
        brands = {p["brand"] for p in products}
        print(f"  Unique brands: {', '.join(sorted(brands))}")
    
    print("\n" + "="*60)
    print("VALIDATION PASSED" if total_products >= 30 else "WARNING: < 30 products")
    print("="*60)


# OOS candidates for substitution testing (mark these in seed data):
OOS_CANDIDATES = {
    "mp-001": "mp-004",  # Tata Salt → MTR Pasta (for testing low-confidence sub)
    "mp-005": "mp-004",  # Barilla → MTR (for testing high-confidence sub)
    "mp-007": "mp-006",  # Heinz Sauce → Kissan (high-confidence)
    "cl-001": "cl-002",  # Scrubber → Glass Cleaner (medium-confidence)
    "bc-003": "bc-006",  # Pampers → Huggies (high-confidence)
    "ps-002": "ps-001",  # Lay's → Kurkure (medium-confidence)
    "ft-005": "ft-002",  # Protein → Yoga Mat (low-confidence - intentionally wrong)
    "pc-003": "pc-002",  # Pedigree → Whiskas (low-confidence - dog→cat)
    "os-004": "os-002",  # Notebooks → Pens (medium-confidence)
    "gn-001": "gn-003",  # Handwash → Tissue (low-confidence)
}

# Brands that should appear in UserPreference seed data (for personalization testing):
PREFERRED_BRANDS_FOR_SEED_DATA = [
    "Barilla",     # meal_preparation
    "Amul",        # meal_preparation
    "Heinz",       # meal_preparation
    "Pampers",     # baby_care
    "Johnson's",   # baby_care
    "Pedigree",    # pet_care
    "Whiskas",     # pet_care
    "3M",          # office_supplies, cleaning
    "Classmate",   # office_supplies
]


if __name__ == "__main__":
    validate_catalog()
