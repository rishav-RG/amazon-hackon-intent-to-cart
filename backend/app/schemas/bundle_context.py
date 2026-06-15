# app/schemas/bundle_context.py
from typing import List, Optional
from pydantic import BaseModel, Field

class ConfirmedEntity(BaseModel):
    raw: str
    canonical: str
    brand: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None

class ShoppingConstraints(BaseModel):
    quantity: Optional[int] = None
    budget: Optional[float] = None
    brand: Optional[str] = None
    diet: Optional[str] = None

class BundleContext(BaseModel):
    intent_id: str
    intent_type: str
    shopping_theme: Optional[str] = None
    resolved_category: Optional[str] = None
    confirmed_entities: List[ConfirmedEntity] = Field(default_factory=list)
    constraints: ShoppingConstraints = Field(default_factory=ShoppingConstraints)
    semantic_query: Optional[str] = None
    category_query: Optional[str] = None
    product_query_hints: List[str] = Field(default_factory=list)