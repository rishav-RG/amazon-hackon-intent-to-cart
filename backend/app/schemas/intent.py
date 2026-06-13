"""Intent request and response schemas."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# The 8 supported intent types
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


class IntentRequest(BaseModel):
    """Schema for incoming intent classification requests.

    Validates: Requirements 23.1, 23.4
    """

    text: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=1, max_length=255)


class IntentResponse(BaseModel):
    """Schema for intent classification responses.

    Validates: Requirements 23.2, 23.3
    """

    intent_id: UUID
    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: list[str] = Field(default_factory=list, max_length=50)
    clarification_question: str | None = None
    cached_bundle: dict | None = None
