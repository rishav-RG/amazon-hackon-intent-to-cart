"""
Bundle schemas for API requests and responses.

Provides Pydantic models for bundle generation, including metadata
that exists only at runtime (not persisted to database).
"""

from __future__ import annotations
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field


class BundleItemSchema(BaseModel):
    """
    Individual product item within a bundle.
    
    Includes runtime metadata (substitution status, delivery info) that
    is NOT persisted to the database. Only product_id, product_name,
    quantity, and price are stored in BundleItem model.
    """
    product_id: str
    name: str
    brand: str
    category: str
    quantity: int
    unit_price: float
    image_url: str = ""
    
    # Runtime-only fields (not in database)
    is_substituted: bool = False
    original_product_id: Optional[str] = None
    eta_minutes: int
    eta_label: str
    warehouse: str


class BundleSchema(BaseModel):
    """
    Complete bundle with type classification and scoring.
    
    Note: bundle_type is NOT stored in the database (Bundle_Model only has
    id, user_id, intent_id, name, created_at). The type exists only in
    the schema/cache layer.
    """
    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bundle_type: Literal["classic", "budget", "premium"]
    bundle_name: str
    intent_type: str
    items: list[BundleItemSchema]
    total_price: float
    final_score: float = 0.0


class BundleListResponse(BaseModel):
    """
    API response for GET /v1/bundles/{intentId}.
    
    Returns the highest-scored bundle as recommended, plus all options
    sorted by score descending.
    """
    intent_id: str
    recommended: BundleSchema
    options: list[BundleSchema]
    cache_hit: bool = False
