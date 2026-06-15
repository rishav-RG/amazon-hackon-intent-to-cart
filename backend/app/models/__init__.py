"""
SQLAlchemy models package.

Defines the declarative Base and re-exports all model classes
so that Alembic and other consumers can discover them via Base.metadata.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Async declarative base for all SQLAlchemy models."""

    pass


# Import models so they register with Base.metadata
from app.models.intent import Intent_Model  # noqa: E402, F401
from app.models.clarification import Clarification_Model  # noqa: E402, F401
from app.models.substitution import Substitution_Model  # noqa: E402, F401
from app.models.bundle import Bundle_Model, BundleItem  # noqa: E402, F401
from app.models.cart import Cart_Model, CartItem  # noqa: E402, F401
from app.models.user_preference import UserPreference_Model  # noqa: E402, F401

__all__ = [
    "Base",
    "Intent_Model",
    "Clarification_Model",
    "Bundle_Model",
    "BundleItem",
    "Cart_Model",
    "CartItem",
    "Substitution_Model",
    "UserPreference_Model",
]
