# Bundle Schema Draft - Phase 0 Design
# This will become app/schemas/bundle.py in Phase 1
# DO NOT COMMIT TO MAIN - Design reference only

"""
CRITICAL: Review with Dev C before finalizing!
Dev C's CheckoutService will import from this schema.
Any changes after Dev C builds against it = merge conflict.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
import uuid


class BundleItemSchema(BaseModel):
    """
    Represents a single product item within a bundle.
    
    Field Design Decisions:
    - product_id: str (not UUID) - matches mock catalog keys
    - is_substituted: bool - flagged by SubstitutionEngine when OOS
    - original_product_id: Optional - populated only when auto-replaced
    - eta_minutes/eta_label: added by router after ETAAdapter call
    - warehouse: added by router after InventoryAdapter call
    """
    product_id: str
    name: str
    brand: str
    category: str
    quantity: int
    unit_price: float
    is_substituted: bool = False
    original_product_id: Optional[str] = None  # Set when is_substituted=True and auto-replaced
    eta_minutes: int
    eta_label: str
    warehouse: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "mp-001",
                "name": "Barilla Spaghetti 500g",
                "brand": "Barilla",
                "category": "pasta",
                "quantity": 1,
                "unit_price": 85.0,
                "is_substituted": False,
                "original_product_id": None,
                "eta_minutes": 35,
                "eta_label": "In 35 min",
                "warehouse": "WH-A",
            }
        }
    }


class BundleSchema(BaseModel):
    """
    Represents a complete product bundle (classic, budget, or premium).
    
    Field Design Decisions:
    - bundle_id: UUID auto-generated, becomes DB primary key after persist
    - bundle_type: Literal type for strict validation
    - final_score: 0.0-1.0 float from RankingEngine, used for sorting
    - intent_type: copied from Intent model for context
    """
    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bundle_type: Literal["classic", "budget", "premium"]
    bundle_name: str
    intent_type: str
    items: list[BundleItemSchema]
    total_price: float
    final_score: float = 0.0  # Set by RankingEngine, used for sorting
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "bundle_id": "550e8400-e29b-41d4-a716-446655440000",
                "bundle_type": "classic",
                "bundle_name": "Meal Preparation — Classic",
                "intent_type": "meal_preparation",
                "items": [
                    # ... BundleItemSchema examples
                ],
                "total_price": 305.0,
                "final_score": 0.847,
            }
        }
    }


class BundleListResponse(BaseModel):
    """
    API response schema for GET /v1/bundles/{intentId}.
    
    Field Design Decisions:
    - recommended: always the bundle with highest final_score
    - options: all 3 bundles sorted by final_score descending
    - cache_hit: false on first call, true on subsequent cached calls
    """
    intent_id: str
    recommended: BundleSchema
    options: list[BundleSchema]
    cache_hit: bool = False
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "intent_id": "550e8400-e29b-41d4-a716-446655440000",
                "recommended": {
                    # ... highest scored bundle
                },
                "options": [
                    # ... all 3 bundles sorted
                ],
                "cache_hit": False,
            }
        }
    }


# Questions for Dev C before Phase 1 commit:
"""
1. Does CheckoutService need any additional fields on BundleItemSchema?
   - unit (e.g., "pack", "bottle")?
   - availability status?
   - substitution confidence score?

2. Does BundleSchema need any additional fields?
   - created_at timestamp?
   - user_id reference?
   - bundle description/tagline?

3. Should bundle_id be string UUID or actual UUID type?
   Current: str (easier for JSON serialization)
   Alternative: uuid.UUID (type safety)

4. Should BundleListResponse include metadata?
   - generation_time_ms?
   - personalization_applied?
   - substitution_count?

5. Naming conventions:
   - snake_case (current) or camelCase?
   - "bundle_id" or "bundleId"?

DECISION LOG:
- [Date] Dev C confirmed: no additional fields needed
- [Date] Agreed on snake_case for all field names
- [Date] bundle_id will be string type
"""


# Type aliases for internal use (optional):
BundleList = list[BundleSchema]
