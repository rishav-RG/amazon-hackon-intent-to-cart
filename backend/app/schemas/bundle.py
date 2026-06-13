"""
Bundle schemas for API request/response validation.
Developer B owns this file.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field
import uuid


class BundleItemSchema(BaseModel):
    """
    Represents a single product item within a bundle.
    
    Fields:
        product_id: Product identifier from catalog
        name: Product display name
        brand: Brand name
        category: Product category
        quantity: Number of units
        unit_price: Price per unit in INR
        is_substituted: True if product was substituted due to OOS
        original_product_id: Original product ID if substituted
        eta_minutes: Estimated delivery time in minutes
        eta_label: Human-readable delivery time
        warehouse: Warehouse identifier
    """
    product_id: str
    name: str
    brand: str
    category: str
    quantity: int
    unit_price: float
    is_substituted: bool = False
    original_product_id: Optional[str] = None
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
    Represents a complete product bundle.
    
    Fields:
        bundle_id: Unique bundle identifier (UUID)
        bundle_type: Bundle tier (classic, budget, or premium)
        bundle_name: Display name for the bundle
        intent_type: Intent category this bundle was generated for
        items: List of products in the bundle
        total_price: Sum of all item prices
        final_score: Ranking score from RankingEngine (0.0-1.0)
    """
    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bundle_type: Literal["classic", "budget", "premium"]
    bundle_name: str
    intent_type: str
    items: list[BundleItemSchema]
    total_price: float
    final_score: float = 0.0
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "bundle_id": "550e8400-e29b-41d4-a716-446655440000",
                "bundle_type": "classic",
                "bundle_name": "Meal Preparation — Classic",
                "intent_type": "meal_preparation",
                "items": [],
                "total_price": 305.0,
                "final_score": 0.847,
            }
        }
    }


class BundleListResponse(BaseModel):
    """
    API response for GET /v1/bundles/{intentId}.
    
    Fields:
        intent_id: Intent UUID this response is for
        recommended: Highest-scored bundle
        options: All 3 bundles sorted by score (descending)
        cache_hit: True if result came from cache
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
                    "bundle_id": "bundle-1",
                    "bundle_type": "classic",
                    "bundle_name": "Classic Bundle",
                    "intent_type": "meal_preparation",
                    "items": [],
                    "total_price": 300.0,
                    "final_score": 0.9,
                },
                "options": [],
                "cache_hit": False,
            }
        }
    }
