"""
BigBasket Catalog Preparation Script.

Reads the raw BigBasket.csv, curates ~150 products, computes embeddings,
generates substitution mappings, and outputs JSON + numpy files.

Usage:
    cd backend
    python scripts/prepare_catalog.py

Outputs:
    seed_data/bigbasket_catalog.json      — curated product catalog
    seed_data/product_embeddings.npy      — 384-dim embedding vectors
    seed_data/category_mapping.json       — BigBasket category → intent type
    seed_data/auto_substitutions.json     — product swap pairs
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

SEED_DIR = Path(__file__).parent.parent / "seed_data"
CSV_PATH = SEED_DIR / "BigBasket.csv"
PRODUCTS_PER_CATEGORY = 15  # ~15 products per category = ~150 total
MODEL_NAME = "all-MiniLM-L6-v2"

# BigBasket category → intent type mapping
CATEGORY_MAPPING = {
    "Fruits & Vegetables": "meal_preparation",
    "Foodgrains, Oil & Masala": "meal_preparation",
    "Bakery, Cakes & Dairy": "meal_preparation",
    "Eggs, Meat & Fish": "meal_preparation",
    "Gourmet & World Food": "meal_preparation",
    "Beverages": "general",
    "Snacks & Branded Foods": "party_supplies",
    "Beauty & Hygiene": "general",
    "Cleaning & Household": "cleaning",
    "Kitchen, Garden & Pets": "pet_care",
    "Baby Care": "baby_care",
}


def load_and_clean(csv_path: Path) -> pd.DataFrame:
    """Load CSV and clean data."""
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"  Raw rows: {len(df)}")

    # Drop rows with missing critical fields
    df = df.dropna(subset=["ProductName", "Brand", "Price", "Category", "SubCategory"])

    # Ensure Price is numeric
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["DiscountPrice"] = pd.to_numeric(df["DiscountPrice"], errors="coerce")
    df = df.dropna(subset=["Price"])
    df = df[df["Price"] > 0]

    print(f"  Clean rows: {len(df)}")
    return df


def curate_products(df: pd.DataFrame, per_category: int) -> pd.DataFrame:
    """
    Select diverse products from each category.

    Strategy:
    - From each category, pick products with diverse brands and price ranges
    - Prefer products with images (better for demo)
    - Sort by price within category for tier diversity
    """
    print(f"\nCurating {per_category} products per category...")
    curated = []

    for category in CATEGORY_MAPPING.keys():
        cat_df = df[df["Category"] == category].copy()

        if len(cat_df) == 0:
            print(f"  {category}: 0 products (skipping)")
            continue

        # Prefer products with images
        has_image = cat_df[cat_df["Image_Url"].notna() & (cat_df["Image_Url"] != "")]
        if len(has_image) >= per_category:
            cat_df = has_image

        # Get diverse brands: pick at most 2 per brand to ensure variety
        diverse = cat_df.groupby("Brand").head(2)

        # Sort by price and pick evenly (cheap + mid + expensive)
        diverse = diverse.sort_values("Price")

        if len(diverse) >= per_category:
            # Take evenly spaced indices for price diversity
            indices = np.linspace(0, len(diverse) - 1, per_category, dtype=int)
            selected = diverse.iloc[indices]
        else:
            selected = diverse.head(per_category)

        curated.append(selected)
        print(f"  {category}: {len(selected)} products selected")

    result = pd.concat(curated, ignore_index=True)
    print(f"\n  Total curated: {len(result)} products")
    return result


def build_catalog(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to product catalog list."""
    products = []
    for idx, row in df.iterrows():
        product = {
            "product_id": f"BB-{idx:04d}",
            "name": str(row["ProductName"]).strip(),
            "brand": str(row["Brand"]).strip(),
            "price": round(float(row["Price"]), 2),
            "discount_price": round(float(row["DiscountPrice"]), 2) if pd.notna(row["DiscountPrice"]) else None,
            "unit": str(row["Quantity"]).strip() if pd.notna(row["Quantity"]) else "",
            "category": str(row["Category"]).strip(),
            "sub_category": str(row["SubCategory"]).strip(),
            "intent_type": CATEGORY_MAPPING.get(str(row["Category"]).strip(), "general"),
            "image_url": str(row["Image_Url"]).strip() if pd.notna(row["Image_Url"]) else "",
            "product_url": str(row["Absolute_Url"]).strip() if pd.notna(row["Absolute_Url"]) else "",
        }
        products.append(product)
    return products


def compute_embeddings(products: list[dict], model_name: str) -> np.ndarray:
    """Compute sentence embeddings for all products."""
    print(f"\nComputing embeddings with {model_name}...")
    model = SentenceTransformer(model_name)

    # Build rich text for each product (name + brand + categories)
    texts = []
    for p in products:
        text = f"{p['name']} {p['brand']} {p['category']} {p['sub_category']}"
        texts.append(text)

    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    print(f"  Embeddings shape: {embeddings.shape}")
    return embeddings


def generate_substitutions(products: list[dict]) -> list[dict]:
    """
    Generate substitution mappings.

    Logic: For each product, find alternatives in the same SubCategory
    with different brand and similar price (±30%).
    """
    print("\nGenerating substitution mappings...")
    substitutions = []

    # Group by sub_category
    from collections import defaultdict
    by_subcat = defaultdict(list)
    for p in products:
        by_subcat[p["sub_category"]].append(p)

    for sub_cat, items in by_subcat.items():
        if len(items) < 2:
            continue

        for i, product in enumerate(items):
            for j, candidate in enumerate(items):
                if i == j:
                    continue
                # Different brand
                if candidate["brand"] == product["brand"]:
                    continue
                # Similar price (±30%)
                price_ratio = candidate["price"] / product["price"] if product["price"] > 0 else 0
                if 0.7 <= price_ratio <= 1.3:
                    substitutions.append({
                        "original_product_id": product["product_id"],
                        "replacement_product_id": candidate["product_id"],
                        "original_name": product["name"],
                        "replacement_name": candidate["name"],
                        "sub_category": sub_cat,
                        "price_diff": round(candidate["price"] - product["price"], 2),
                    })

    # Deduplicate (keep first occurrence per original)
    seen = set()
    unique = []
    for sub in substitutions:
        key = (sub["original_product_id"], sub["replacement_product_id"])
        if key not in seen:
            seen.add(key)
            unique.append(sub)

    print(f"  Generated {len(unique)} substitution pairs")
    return unique


def main():
    """Run the full catalog preparation pipeline."""
    print("=" * 60)
    print("  BigBasket Catalog Preparation")
    print("=" * 60)

    # Step 1: Load and clean
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found!")
        sys.exit(1)

    df = load_and_clean(CSV_PATH)

    # Step 2: Curate products
    curated_df = curate_products(df, PRODUCTS_PER_CATEGORY)

    # Step 3: Build catalog
    products = build_catalog(curated_df)

    # Step 4: Compute embeddings
    embeddings = compute_embeddings(products, MODEL_NAME)

    # Step 5: Generate substitutions
    substitutions = generate_substitutions(products)

    # Step 6: Save outputs
    print("\nSaving outputs...")

    catalog_path = SEED_DIR / "bigbasket_catalog.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"  ✓ {catalog_path} ({len(products)} products)")

    embeddings_path = SEED_DIR / "product_embeddings.npy"
    np.save(embeddings_path, embeddings)
    print(f"  ✓ {embeddings_path} ({embeddings.shape})")

    mapping_path = SEED_DIR / "category_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(CATEGORY_MAPPING, f, indent=2)
    print(f"  ✓ {mapping_path}")

    subs_path = SEED_DIR / "auto_substitutions.json"
    with open(subs_path, "w", encoding="utf-8") as f:
        json.dump(substitutions, f, indent=2, ensure_ascii=False)
    print(f"  ✓ {subs_path} ({len(substitutions)} pairs)")

    print("\n" + "=" * 60)
    print("  Done! Catalog prepared successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
