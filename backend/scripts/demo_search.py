"""
Demo: Test semantic product search offline (no Redis/Postgres needed).
Run: python scripts/demo_search.py
"""
import sys, os
sys.path.insert(0, ".")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("GEMINI_API_KEY", "test")

from app.services.product_catalog import get_product_catalog

output_lines = []

def p(text=""):
    output_lines.append(text)

p("=" * 70)
p("  SEMANTIC PRODUCT SEARCH DEMO")
p("  (Uses pre-computed embeddings from BigBasket data)")
p("=" * 70)

catalog = get_product_catalog()
p(f"\n  Catalog loaded: {len(catalog.products)} products")
p(f"  Embeddings shape: {catalog.embeddings.shape}")

queries = [
    ("I need dal and rice for dinner", "meal_preparation"),
    ("protein bars for gym workout", "general"),
    ("baby shampoo and lotion", "baby_care"),
    ("cleaning supplies for bathroom", "cleaning"),
    ("party snacks and cold drinks", "party_supplies"),
    ("cat food and pet shampoo", "pet_care"),
]

for query, intent in queries:
    p(f"\n{'-' * 70}")
    p(f"  Query: \"{query}\"")
    p(f"  Intent: {intent}")
    p(f"{'-' * 70}")
    
    # Combined search (semantic + category filter)
    results = catalog.search_combined(query, intent, top_k=5)
    
    for i, r in enumerate(results, 1):
        score = r.get('score', 0)
        name = r['name'][:42]
        brand = r['brand'][:12]
        price = r['price']
        p(f"  {i}. [{score:.3f}] {name:42s} | {brand:12s} | Rs.{price}")

p(f"\n{'=' * 70}")
p("  DEMO COMPLETE")
p(f"{'=' * 70}")

# Write to file
with open("scripts/demo_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))
