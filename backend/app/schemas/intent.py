"""Intent request and response schemas."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# The 8 supported intent types (UNCHANGED — preserves DB + response validation)
IntentType = Literal[
    "add_to_cart",
    "remove_from_cart",
    "search_product",
    "reorder",
    "substitute",
    "compare",
    "get_recommendation",
    "checkout",
]


# NEW: The 5 parser intent types the LLM is allowed to emit.
# These are mapped to the existing IntentType enum before building responses,
# so the Literal validation above never breaks.
PARSER_TO_INTENT: dict[str, str] = {
    "search_product": "search_product",
    "recommendation_request": "get_recommendation",
    "add_to_cart": "add_to_cart",
    "build_bundle": "add_to_cart",
    "compare_products": "compare",
}


class ShoppingConstraints(BaseModel):
    """NEW: Structured slot constraints extracted by the LLM parser.

    All fields optional/nullable so absence is the backward-compatible default.
    """

    quantity: int | None = None
    budget: float | None = None
    brand: str | None = None
    diet: str | None = None


class IntentRequest(BaseModel):
    """Schema for incoming intent classification requests.

    Validates: Requirements 23.1, 23.4
    """

    text: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=1, max_length=255)


class IntentResponse(BaseModel):
    """Schema for intent classification responses.

    Validates: Requirements 23.2, 23.3

    Existing fields are unchanged. New optional fields (shopping_theme,
    constraints, resolved_category, needs_clarification) default to values
    that preserve the original response shape and behavior.
    """

    intent_id: UUID
    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: list[str] = Field(default_factory=list, max_length=50)
    clarification_question: str | None = None
    cached_bundle: dict | None = None
    llm_used: bool = False
    fallback: bool = False

    # ── NEW optional fields (backward-compatible) ──
    shopping_theme: str | None = None
    constraints: ShoppingConstraints | None = None
    resolved_category: str | None = None
    needs_clarification: bool = False
