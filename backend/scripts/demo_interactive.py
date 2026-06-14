"""
Interactive Demo - Test the full Intent-to-Cart pipeline locally.

NO Redis or Postgres needed. Runs entirely in-memory.

Usage:
    cd backend
    .venv\\Scripts\\python.exe scripts\\demo_interactive.py

Type natural language queries and see:
- Intent classification (keyword + semantic)
- Product search (semantic similarity from BigBasket data)
- Bundle generation (budget/classic/premium)
"""

import sys
import os

sys.path.insert(0, ".")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("GEMINI_API_KEY", "")

import asyncio
from app.services.intent_engine import classify, classify_hybrid, FAST_PATH_THRESHOLD
from app.services.product_catalog import get_product_catalog


def run_keyword_classification(text):
    """Run keyword-only classification."""
    result = classify(text)
    return {
        "intent_type": result.intent_type,
        "confidence": result.confidence,
        "entities": result.entities,
    }


def run_product_search(query, intent_type, top_k=10):
    """Run semantic product search."""
    catalog = get_product_catalog()
    return catalog.search_combined(query, intent_type, top_k=top_k)


def generate_bundles(products):
    """Create simple budget/classic/premium bundles from products."""
    if not products:
        return []

    # Sort by price
    sorted_products = sorted(products, key=lambda p: p["price"])

    bundles = []

    # Budget: 4 cheapest
    budget_items = sorted_products[:4]
    bundles.append({
        "tier": "BUDGET",
        "items": budget_items,
        "total": sum(p["price"] for p in budget_items),
    })

    # Classic: middle 5
    mid_start = len(sorted_products) // 4
    classic_items = sorted_products[mid_start:mid_start + 5]
    bundles.append({
        "tier": "CLASSIC (Recommended)",
        "items": classic_items,
        "total": sum(p["price"] for p in classic_items),
    })

    # Premium: 4 most expensive
    premium_items = sorted_products[-4:]
    bundles.append({
        "tier": "PREMIUM",
        "items": premium_items,
        "total": sum(p["price"] for p in premium_items),
    })

    return bundles


def main():
    print()
    print("=" * 60)
    print("   INTENT-TO-CART: Interactive Demo")
    print("   (No Redis/Postgres needed)")
    print("=" * 60)
    print()
    print("  Type a shopping query and see the full pipeline in action.")
    print("  Type 'quit' to exit.")
    print()

    # Pre-load catalog
    catalog = get_product_catalog()
    print(f"  Catalog loaded: {len(catalog.products)} BigBasket products")
    print()

    while True:
        print("-" * 60)
        user_input = input("  You: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n  Bye!")
            break

        print()

        # Step 1: Intent Classification
        print("  [1] INTENT CLASSIFICATION")
        keyword_result = run_keyword_classification(user_input)
        print(f"      Keyword: {keyword_result['intent_type']} (confidence: {keyword_result['confidence']:.2f})")

        if keyword_result["confidence"] >= FAST_PATH_THRESHOLD:
            print(f"      -> FAST PATH (confidence >= {FAST_PATH_THRESHOLD})")
            intent_type = keyword_result["intent_type"]
            method = "keyword"
        else:
            print(f"      -> Low confidence, would call Gemini LLM in production")
            # Use keyword result as fallback (no LLM without API key)
            intent_type = keyword_result["intent_type"]
            method = "keyword (LLM unavailable in demo)"

        entities = keyword_result["entities"]
        print(f"      Intent: {intent_type}")
        print(f"      Entities: {entities}")
        print(f"      Method: {method}")
        print()

        # Step 2: Product Search
        print("  [2] SEMANTIC PRODUCT SEARCH")
        # Use entities + original text for better search
        search_query = " ".join(entities) if entities else user_input
        products = run_product_search(search_query, intent_type, top_k=10)
        print(f"      Query: \"{search_query}\"")
        print(f"      Found: {len(products)} products")
        print()
        print(f"      {'#':>3} {'Score':>6} | {'Product':<40} | {'Brand':<15} | {'Price':>8}")
        print(f"      {'---':>3} {'------':>6} | {'-'*40} | {'-'*15} | {'--------':>8}")
        for i, p in enumerate(products[:10], 1):
            score = p.get("score", 0)
            name = p["name"][:40]
            brand = p["brand"][:15]
            price = p["price"]
            print(f"      {i:>3} {score:>6.3f} | {name:<40} | {brand:<15} | Rs.{price:>7.1f}")
        print()

        # Step 3: Bundle Generation
        print("  [3] BUNDLE GENERATION")
        bundles = generate_bundles(products[:10])
        for bundle in bundles:
            tier = bundle["tier"]
            total = bundle["total"]
            print(f"      [{tier}] Total: Rs.{total:.0f}")
            for item in bundle["items"]:
                print(f"        - {item['name'][:45]} (Rs.{item['price']})")
            print()

        print("  [DONE] Ready for cart + checkout")
        print()


if __name__ == "__main__":
    main()
