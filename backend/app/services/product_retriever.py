"""
Product Retriever — Product Retrieval stage of the hybrid pipeline.

Given resolved category + user entities, retrieves the most relevant products
from the real BigBasket catalog (via ProductCatalog) and normalizes them into
the dict shape BundleGenerator expects.

Reuses ProductCatalog.search_combined() (semantic search + category filter),
which already exists. This module only adapts the output shape and applies
optional constraint filtering (budget/brand).
"""

import logging
from typing import Optional

from app.services.product_catalog import get_product_catalog

logger = logging.getLogger(__name__)


# Keys BundleGenerator._create_bundle expects on each product dict:
#   product_id, name, brand, category, price
def _normalize(product: dict) -> dict:
    """Map a catalog product into the dict shape BundleGenerator expects."""
    return {
        "product_id": product.get("product_id", ""),
        "name": product.get("name", "Unknown"),
        "brand": product.get("brand", "Unknown"),
        # Use sub_category as the "category" for personalization granularity,
        # fall back to top-level category, then intent_type.
        "category": (
            product.get("sub_category")
            or product.get("category")
            or product.get("intent_type", "general")
        ),
        "price": float(product.get("price", 0.0) or 0.0),
        "unit": product.get("unit", ""),
    }


def _apply_constraints(products: list[dict], constraints: dict) -> list[dict]:
    """Apply optional budget/brand constraints (non-destructive: keeps order)."""
    if not constraints:
        return products

    filtered = products

    budget = constraints.get("budget")
    if isinstance(budget, (int, float)) and budget > 0:
        within = [p for p in filtered if p["price"] <= budget]
        if within:  # only apply if it leaves something usable
            filtered = within

    brand = constraints.get("brand")
    if isinstance(brand, str) and brand.strip():
        brand_l = brand.strip().lower()
        preferred = [p for p in filtered if brand_l in p["brand"].lower()]
        # Boost preferred brand to front, keep others as fallback
        if preferred:
            others = [p for p in filtered if p not in preferred]
            filtered = preferred + others

    return filtered


def retrieve(
    entities: list[str],
    category: str,
    constraints: Optional[dict] = None,
    semantic_query: Optional[str] = None,
    top_k: int = 12,
) -> Optional[list[dict]]:
    """
    Retrieve products for a resolved category, ranked by relevance to entities.

    Args:
        entities: extracted product entities (e.g. ["protein bars", "almond milk"])
        category: resolved catalog category / intent_type (e.g. "fitness")
        constraints: optional {quantity, budget, brand, diet}
        top_k: max products to return

    Returns:
        List of normalized product dicts (BundleGenerator-compatible), or
        None if retrieval is not possible (caller falls back to MOCK_CATALOG).
    """
    try:
        catalog = get_product_catalog()
    except Exception as exc:
        logger.warning("ProductCatalog unavailable: %s — retriever skipped", exc)
        return None

    # Build a query string from semantic hints first, then entities, then category
    if semantic_query and semantic_query.strip():
        query = semantic_query.strip()
    else:
        query = " ".join(entities).strip() if entities else category.replace("_", " ")

    try:
        # search_combined = semantic search + category filter (already exists)
        results = catalog.search_combined(query=query, intent_type=category, top_k=top_k)
    except Exception as exc:
        logger.warning("search_combined failed (%s) — trying category-only", exc)
        try:
            results = catalog.get_by_intent(category, limit=top_k)
        except Exception as exc2:
            logger.warning("get_by_intent failed too: %s — retriever returns None", exc2)
            return None

    if not results:
        logger.info("Retriever found no products for category=%s query=%s", category, query)
        return None

    normalized = [_normalize(p) for p in results]
    normalized = _apply_constraints(normalized, constraints or {})

    # De-duplicate by product_id, preserve order
    seen, deduped = set(), []
    for p in normalized:
        if p["product_id"] and p["product_id"] not in seen:
            seen.add(p["product_id"])
            deduped.append(p)

    return deduped or None
