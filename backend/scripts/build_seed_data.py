"""
Build final seed data: catalog, category descriptions, embeddings, substitutions.

Run from backend/:
    python scripts/build_seed_data.py

Outputs:
    seed_data/bigbasket_catalog.json       — curated product catalog (200+ products)
    seed_data/product_embeddings.npy       — (N, 384) product embeddings
    seed_data/category_descriptions.json   — rich text descriptions per intent category
    seed_data/category_embeddings.npy      — (num_categories, 384) category embeddings
    seed_data/category_mapping.json        — BigBasket category → intent_type mapping (updated)
    seed_data/auto_substitutions.json      — substitution pairs within same sub_category
    seed_data/user_preferences.json        — kept as-is
"""

import csv
import json
import hashlib
import random
from pathlib import Path
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer

SEED_DIR = Path(__file__).parent.parent / "seed_data"
CSV_PATH = SEED_DIR / "BigBasket.csv"

# ──────────────────────────────────────────────────────────────────────────────
# 1. CATEGORY SYSTEM
# ──────────────────────────────────────────────────────────────────────────────

# Updated category mapping: BigBasket category → intent_type
# Now includes "fitness" and "beverages_snacks" as proper categories
CATEGORY_MAPPING = {
    "Fruits & Vegetables": "meal_preparation",
    "Foodgrains, Oil & Masala": "meal_preparation",
    "Bakery, Cakes & Dairy": "meal_preparation",
    "Eggs, Meat & Fish": "meal_preparation",
    "Gourmet & World Food": "meal_preparation",
    "Beverages": "beverages_snacks",
    "Snacks & Branded Foods": "beverages_snacks",
    "Beauty & Hygiene": "personal_care",
    "Cleaning & Household": "cleaning",
    "Kitchen, Garden & Pets": "pet_care",
    "Baby Care": "baby_care",
}

# Rich category descriptions for semantic matching
# These get embedded so shopping_themes can match to the right category
CATEGORY_DESCRIPTIONS = {
    "meal_preparation": (
        "Cooking ingredients, fresh vegetables, fruits, rice, wheat, atta, "
        "pasta, oils, ghee, spices, masala, dairy, milk, paneer, curd, eggs, "
        "meat, chicken, fish, seafood, baking supplies, gourmet food, "
        "breakfast items, lunch dinner recipes, meal prep, grocery staples"
    ),
    "beverages_snacks": (
        "Tea, coffee, green tea, juice, soft drinks, energy drinks, "
        "protein shakes, milkshakes, soya milk, flavoured milk, "
        "chips, namkeen, biscuits, cookies, snack bars, protein bars, "
        "nuts, dried fruits, munchies, party snacks, ready to eat, "
        "instant noodles, popcorn, crackers"
    ),
    "personal_care": (
        "Shampoo, conditioner, soap, body wash, face wash, moisturizer, "
        "sunscreen, deodorant, perfume, toothpaste, toothbrush, "
        "hair oil, hair color, makeup, cosmetics, skin care, lip care, "
        "men grooming, shaving, feminine hygiene, hand sanitizer"
    ),
    "cleaning": (
        "Floor cleaner, toilet cleaner, dish wash, detergent, "
        "laundry liquid, fabric softener, surface cleaner, glass cleaner, "
        "mops, brooms, scrubbers, sponges, trash bags, tissues, "
        "air freshener, pest control, disinfectant, bathroom cleaner"
    ),
    "baby_care": (
        "Baby diapers, baby wipes, baby food, infant formula, "
        "baby shampoo, baby lotion, baby cream, baby oil, "
        "baby powder, feeding bottles, teethers, baby bath, "
        "diaper rash cream, baby cereal, organic baby food"
    ),
    "pet_care": (
        "Dog food, cat food, pet treats, pet shampoo, pet toys, "
        "pet accessories, aquarium, bird food, pet grooming, "
        "cat litter, dog biscuits, pet bowls, leash, collar, "
        "garden tools, garden seeds, pots, planters, fertilizer"
    ),
    "fitness": (
        "Protein powder, whey protein, protein bars, energy bars, "
        "sports drinks, electrolyte, BCAA, creatine, pre-workout, "
        "oats, muesli, granola, peanut butter, almond butter, "
        "quinoa, chia seeds, flax seeds, health supplements, "
        "vitamins, omega-3, green superfoods, diet food, low calorie"
    ),
}

# Keywords that help with fast-path matching (before embeddings)
CATEGORY_KEYWORDS = {
    "meal_preparation": [
        "cook", "recipe", "dinner", "lunch", "breakfast", "meal",
        "vegetable", "fruit", "rice", "atta", "flour", "oil", "ghee",
        "spice", "masala", "paneer", "egg", "chicken", "fish", "meat",
        "dal", "lentil", "pasta", "noodle", "bread", "roti", "curry"
    ],
    "beverages_snacks": [
        "tea", "coffee", "juice", "drink", "soda", "water", "milk",
        "shake", "smoothie", "chips", "namkeen", "biscuit", "cookie",
        "snack", "munch", "popcorn", "nuts", "bar", "cracker",
        "instant", "ready", "noodles", "party"
    ],
    "personal_care": [
        "shampoo", "soap", "face", "skin", "hair", "body", "wash",
        "cream", "lotion", "perfume", "deodorant", "makeup", "cosmetic",
        "toothpaste", "brush", "hygiene", "grooming", "beauty"
    ],
    "cleaning": [
        "clean", "wash", "detergent", "floor", "toilet", "dish",
        "laundry", "mop", "broom", "scrub", "wipe", "trash",
        "disinfect", "surface", "glass", "bathroom"
    ],
    "baby_care": [
        "baby", "diaper", "infant", "newborn", "toddler", "formula",
        "wipes", "feeding", "teether", "rash", "nappy"
    ],
    "pet_care": [
        "dog", "cat", "pet", "puppy", "kitten", "fish", "bird",
        "aquarium", "garden", "plant", "seeds", "pot", "planter"
    ],
    "fitness": [
        "protein", "gym", "workout", "fitness", "muscle", "whey",
        "energy", "sports", "oats", "muesli", "granola", "peanut butter",
        "health", "supplement", "vitamin", "diet", "low calorie",
        "chia", "flax", "quinoa", "bcaa", "creatine"
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# 2. BUILD CURATED CATALOG FROM CSV
# ──────────────────────────────────────────────────────────────────────────────

def load_csv_products() -> list[dict]:
    """Load all products from BigBasket CSV."""
    products = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
    return products


def assign_intent_type(category: str, sub_category: str, name: str) -> str:
    """Assign intent_type based on category + sub_category + product name heuristics."""
    name_lower = name.lower()
    sub_lower = sub_category.lower() if sub_category else ""
    
    # Fitness detection from name/sub_category
    fitness_keywords = ["protein", "whey", "energy bar", "sports", "oats", "muesli",
                        "granola", "peanut butter", "almond butter", "quinoa",
                        "chia", "flax", "supplement", "bcaa", "creatine"]
    if any(kw in name_lower or kw in sub_lower for kw in fitness_keywords):
        return "fitness"
    
    # Use the category mapping
    base_mapping = CATEGORY_MAPPING.get(category, "general")
    return base_mapping


def curate_catalog(all_products: list[dict]) -> list[dict]:
    """
    Select a diverse, balanced catalog of ~200 products.
    
    Strategy:
    - 40-50 from meal_preparation (already well-represented)
    - 25-30 from beverages_snacks
    - 20-25 from personal_care
    - 20-25 from cleaning
    - 15-20 from baby_care
    - 15-20 from pet_care
    - 15-20 from fitness (extracted from protein/health products)
    """
    # Group by assigned intent_type
    by_intent: dict[str, list[dict]] = defaultdict(list)
    
    for prod in all_products:
        intent = assign_intent_type(
            prod["Category"], 
            prod.get("SubCategory", ""),
            prod["ProductName"]
        )
        by_intent[intent].append(prod)
    
    print("Products available per intent_type:")
    for k, v in sorted(by_intent.items(), key=lambda x: -len(x[1])):
        print(f"  {k}: {len(v)}")
    
    # Target counts per category
    targets = {
        "meal_preparation": 50,
        "beverages_snacks": 30,
        "personal_care": 25,
        "cleaning": 25,
        "baby_care": 18,
        "pet_care": 18,
        "fitness": 20,
    }
    
    catalog = []
    product_id_counter = 0
    
    for intent_type, target_count in targets.items():
        available = by_intent.get(intent_type, [])
        
        if not available:
            print(f"  WARNING: No products for {intent_type}")
            continue
        
        # Deduplicate by name (take cheapest variant)
        seen_names = {}
        for prod in available:
            name = prod["ProductName"].strip()
            price = float(prod.get("Price", 0) or 0)
            if name not in seen_names or price < seen_names[name]["price"]:
                seen_names[name] = {"prod": prod, "price": price}
        
        unique_products = [v["prod"] for v in seen_names.values()]
        
        # Diversify by sub_category
        by_sub = defaultdict(list)
        for prod in unique_products:
            by_sub[prod.get("SubCategory", "Other")].append(prod)
        
        # Pick products round-robin from sub-categories
        selected = []
        sub_cats = list(by_sub.keys())
        random.seed(42)  # Reproducible selection
        random.shuffle(sub_cats)
        
        idx = 0
        while len(selected) < target_count and idx < len(sub_cats) * 5:
            sub = sub_cats[idx % len(sub_cats)]
            items = by_sub[sub]
            pick_idx = idx // len(sub_cats)
            if pick_idx < len(items):
                selected.append(items[pick_idx])
            idx += 1
        
        # Convert to catalog format
        for prod in selected[:target_count]:
            price = float(prod.get("Price", 0) or 0)
            discount = float(prod.get("DiscountPrice", 0) or 0)
            
            catalog_entry = {
                "product_id": f"BB-{product_id_counter:04d}",
                "name": prod["ProductName"].strip(),
                "brand": prod.get("Brand", "Unknown").strip(),
                "price": round(discount if discount > 0 else price, 2),
                "discount_price": round(discount, 2) if discount > 0 else None,
                "unit": prod.get("Quantity", "1 unit").strip(),
                "category": prod["Category"].strip(),
                "sub_category": prod.get("SubCategory", "Other").strip(),
                "intent_type": intent_type,
                "image_url": prod.get("Image_Url", "").strip(),
                "product_url": prod.get("Absolute_Url", "").strip(),
            }
            catalog.append(catalog_entry)
            product_id_counter += 1
    
    return catalog


# ──────────────────────────────────────────────────────────────────────────────
# 3. GENERATE EMBEDDINGS
# ──────────────────────────────────────────────────────────────────────────────

def build_product_text(product: dict) -> str:
    """Create rich text for product embedding."""
    parts = [
        product["name"],
        product.get("brand", ""),
        product.get("category", ""),
        product.get("sub_category", ""),
        product.get("intent_type", ""),
    ]
    return " ".join(p for p in parts if p)


def generate_product_embeddings(catalog: list[dict], model: SentenceTransformer) -> np.ndarray:
    """Generate embeddings for all products."""
    texts = [build_product_text(p) for p in catalog]
    print(f"Encoding {len(texts)} product texts...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings.astype(np.float32)


def generate_category_embeddings(descriptions: dict[str, str], model: SentenceTransformer) -> np.ndarray:
    """Generate embeddings for category descriptions."""
    categories = list(descriptions.keys())
    texts = [descriptions[cat] for cat in categories]
    print(f"Encoding {len(texts)} category descriptions...")
    embeddings = model.encode(texts, batch_size=8)
    return embeddings.astype(np.float32), categories


# ──────────────────────────────────────────────────────────────────────────────
# 4. GENERATE SUBSTITUTIONS
# ──────────────────────────────────────────────────────────────────────────────

def generate_substitutions(catalog: list[dict]) -> list[dict]:
    """Generate substitution pairs: products in same sub_category."""
    by_sub = defaultdict(list)
    for prod in catalog:
        by_sub[prod["sub_category"]].append(prod)
    
    substitutions = []
    for sub_cat, products in by_sub.items():
        if len(products) < 2:
            continue
        # Create pairs within same sub_category
        for i in range(len(products)):
            for j in range(i + 1, min(i + 3, len(products))):  # Max 2 substitutes per product
                p1, p2 = products[i], products[j]
                substitutions.append({
                    "original_product_id": p1["product_id"],
                    "replacement_product_id": p2["product_id"],
                    "original_name": p1["name"],
                    "replacement_name": p2["name"],
                    "sub_category": sub_cat,
                    "price_diff": round(p2["price"] - p1["price"], 2),
                })
                substitutions.append({
                    "original_product_id": p2["product_id"],
                    "replacement_product_id": p1["product_id"],
                    "original_name": p2["name"],
                    "replacement_name": p1["name"],
                    "sub_category": sub_cat,
                    "price_diff": round(p1["price"] - p2["price"], 2),
                })
    
    return substitutions


# ──────────────────────────────────────────────────────────────────────────────
# 5. MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("BUILDING SEED DATA")
    print("=" * 60)
    
    # Load model
    print("\n[1/6] Loading sentence-transformers model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Load and curate catalog
    print("\n[2/6] Loading CSV and curating catalog...")
    all_products = load_csv_products()
    print(f"  Loaded {len(all_products)} products from CSV")
    
    catalog = curate_catalog(all_products)
    print(f"  Final catalog: {len(catalog)} products")
    
    # Generate product embeddings
    print("\n[3/6] Generating product embeddings...")
    product_embeddings = generate_product_embeddings(catalog, model)
    print(f"  Shape: {product_embeddings.shape}")
    
    # Generate category embeddings
    print("\n[4/6] Generating category embeddings...")
    category_embeddings, category_order = generate_category_embeddings(CATEGORY_DESCRIPTIONS, model)
    print(f"  Shape: {category_embeddings.shape}")
    print(f"  Categories: {category_order}")
    
    # Generate substitutions
    print("\n[5/6] Generating substitution pairs...")
    substitutions = generate_substitutions(catalog)
    print(f"  Generated {len(substitutions)} substitution pairs")
    
    # Save everything
    print("\n[6/6] Saving files...")
    
    # Catalog
    with open(SEED_DIR / "bigbasket_catalog.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"  ✓ bigbasket_catalog.json ({len(catalog)} products)")
    
    # Product embeddings
    np.save(SEED_DIR / "product_embeddings.npy", product_embeddings)
    print(f"  ✓ product_embeddings.npy {product_embeddings.shape}")
    
    # Category descriptions
    with open(SEED_DIR / "category_descriptions.json", "w", encoding="utf-8") as f:
        json.dump(CATEGORY_DESCRIPTIONS, f, indent=2, ensure_ascii=False)
    print(f"  ✓ category_descriptions.json ({len(CATEGORY_DESCRIPTIONS)} categories)")
    
    # Category embeddings
    np.save(SEED_DIR / "category_embeddings.npy", category_embeddings)
    print(f"  ✓ category_embeddings.npy {category_embeddings.shape}")
    
    # Category order (which row = which category)
    with open(SEED_DIR / "category_order.json", "w", encoding="utf-8") as f:
        json.dump(category_order, f, indent=2)
    print(f"  ✓ category_order.json")
    
    # Category mapping (updated)
    with open(SEED_DIR / "category_mapping.json", "w", encoding="utf-8") as f:
        json.dump(CATEGORY_MAPPING, f, indent=2, ensure_ascii=False)
    print(f"  ✓ category_mapping.json")
    
    # Category keywords
    with open(SEED_DIR / "category_keywords.json", "w", encoding="utf-8") as f:
        json.dump(CATEGORY_KEYWORDS, f, indent=2, ensure_ascii=False)
    print(f"  ✓ category_keywords.json")
    
    # Auto substitutions
    with open(SEED_DIR / "auto_substitutions.json", "w", encoding="utf-8") as f:
        json.dump(substitutions, f, indent=2, ensure_ascii=False)
    print(f"  ✓ auto_substitutions.json ({len(substitutions)} pairs)")
    
    # Remove precomputed_bundles.json (bundles are dynamic now)
    precomputed_path = SEED_DIR / "precomputed_bundles.json"
    if precomputed_path.exists():
        precomputed_path.unlink()
        print(f"  ✓ REMOVED precomputed_bundles.json (bundles are dynamic)")
    
    # Summary
    print("\n" + "=" * 60)
    print("DONE! Final seed data:")
    print("=" * 60)
    
    intent_counts = defaultdict(int)
    for p in catalog:
        intent_counts[p["intent_type"]] += 1
    
    print(f"\nProducts per category:")
    for cat, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    print(f"\nTotal products: {len(catalog)}")
    print(f"Total categories: {len(CATEGORY_DESCRIPTIONS)}")
    print(f"Total substitutions: {len(substitutions)}")
    print(f"Embedding dim: 384 (all-MiniLM-L6-v2)")


if __name__ == "__main__":
    main()
