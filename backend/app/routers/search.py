"""
Search Router — The main endpoint for Intent-to-Cart.

POST /v1/search: Takes a natural language query, classifies intent,
searches products semantically, and returns bundles ready for cart.

This is the single endpoint the frontend search bar calls.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_current_user_id
from app.services.intent_engine import classify, classify_hybrid, FAST_PATH_THRESHOLD
from app.services.product_catalog import get_product_catalog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["search"])


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response Schemas
# ──────────────────────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class ProductResult(BaseModel):
    product_id: str
    name: str
    brand: str
    price: float
    discount_price: Optional[float] = None
    unit: str = ""
    category: str = ""
    sub_category: str = ""
    image_url: str = ""
    product_url: str = ""
    score: float = 0.0


class BundleResult(BaseModel):
    tier: str  # "budget", "classic", "premium"
    items: list[ProductResult]
    total: float


class IntentResult(BaseModel):
    intent_type: str
    confidence: float
    entities: list[str] = []
    llm_used: bool = False
    fallback: bool = False


class SearchResponse(BaseModel):
    intent: IntentResult
    products: list[ProductResult]
    bundles: list[BundleResult]
    query: str
    total_results: int
    clarification_question: Optional[str] = None
    needs_clarification: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    AI-powered product search.

    1. Classifies the user's intent (keyword → Gemini → semantic fallback)
    2. Searches products semantically using BigBasket embeddings
    3. Generates 3-tier bundles (budget/classic/premium)
    4. Returns everything in one response for the frontend

    No database needed for this endpoint — all in-memory.
    """
    query = body.query.strip()

    # ──────────────────────────────────────────────────────────────────────────
    # Step 1: Intent Classification
    # ──────────────────────────────────────────────────────────────────────────

    try:
        result = await classify_hybrid(query)
        intent = IntentResult(
            intent_type=result.intent_type,
            confidence=result.confidence,
            entities=result.entities,
            llm_used=result.llm_used,
            fallback=result.fallback,
        )
    except Exception as exc:
        logger.error("Intent classification failed: %s", exc)
        # Fallback to keyword-only
        kw_result = classify(query)
        intent = IntentResult(
            intent_type=kw_result.intent_type,
            confidence=kw_result.confidence,
            entities=kw_result.entities,
            llm_used=False,
            fallback=True,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Step 2: Check if clarification needed (confidence < 0.5 AND not a fallback)
    # ──────────────────────────────────────────────────────────────────────────

    if intent.confidence < 0.5 and not intent.fallback:
        # Only ask for clarification if we're confident the intent is wrong
        # (not just because LLM/semantic failed)
        clarification_q = None
        try:
            from app.services.clarification_engine import get_next_question_smart
            clarification_q = await get_next_question_smart(
                user_text=query,
                intent_type=intent.intent_type,
                confidence=intent.confidence,
                entities=intent.entities,
                previous_questions=[],
                answered_count=0,
            )
        except Exception:
            pass

        if not clarification_q:
            from app.services.clarification_engine import get_first_question
            try:
                clarification_q = get_first_question(intent.intent_type)
            except Exception:
                clarification_q = "Could you tell me more about what you're looking for?"

        return SearchResponse(
            intent=intent,
            products=[],
            bundles=[],
            query=query,
            total_results=0,
            clarification_question=clarification_q,
            needs_clarification=True,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Step 3: Semantic Product Search
    # ──────────────────────────────────────────────────────────────────────────

    catalog = get_product_catalog()

    # Build search query from entities + original query
    search_query = " ".join(intent.entities) if intent.entities else query

    # Combined search (semantic similarity + category filter)
    raw_products = catalog.search_combined(search_query, intent.intent_type, top_k=15)

    # Convert to response schema
    products = [
        ProductResult(
            product_id=p["product_id"],
            name=p["name"],
            brand=p["brand"],
            price=p["price"],
            discount_price=p.get("discount_price"),
            unit=p.get("unit", ""),
            category=p.get("category", ""),
            sub_category=p.get("sub_category", ""),
            image_url=p.get("image_url", ""),
            product_url=p.get("product_url", ""),
            score=p.get("score", 0.0),
        )
        for p in raw_products
    ]

    # ──────────────────────────────────────────────────────────────────────────
    # Step 3: Bundle Generation
    # ──────────────────────────────────────────────────────────────────────────

    bundles = _generate_bundles(products)

    return SearchResponse(
        intent=intent,
        products=products,
        bundles=bundles,
        query=query,
        total_results=len(products),
    )


def _generate_bundles(products: list[ProductResult]) -> list[BundleResult]:
    """Generate budget/classic/premium bundles from product results."""
    if len(products) < 3:
        return []

    sorted_products = sorted(products, key=lambda p: p.price)

    bundles = []

    # Budget: 4 cheapest
    budget_items = sorted_products[:4]
    bundles.append(BundleResult(
        tier="budget",
        items=budget_items,
        total=round(sum(p.price for p in budget_items), 2),
    ))

    # Classic: middle 5 (recommended)
    mid = len(sorted_products) // 4
    classic_items = sorted_products[mid:mid + 5]
    if len(classic_items) < 3:
        classic_items = sorted_products[1:6]
    bundles.append(BundleResult(
        tier="classic",
        items=classic_items,
        total=round(sum(p.price for p in classic_items), 2),
    ))

    # Premium: 4 most expensive
    premium_items = sorted_products[-4:]
    bundles.append(BundleResult(
        tier="premium",
        items=premium_items,
        total=round(sum(p.price for p in premium_items), 2),
    ))

    return bundles
