"""
Stub ORM models for unit tests.

Plain Python classes that mirror the expected schema without requiring
SQLAlchemy or a real database connection.
"""
from uuid import uuid4


class Cart:
    """Stub Cart model matching design schema."""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", str(uuid4()))
        self.user_id: str = kwargs.get("user_id", "")
        self.bundle_id: str | None = kwargs.get("bundle_id", None)
        self.status: str = kwargs.get("status", "active")
        self.version: int = kwargs.get("version", 0)
        self.items: list = kwargs.get("items", [])


class CartItem:
    """Stub CartItem model matching design schema."""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", str(uuid4()))
        self.cart_id: str = kwargs.get("cart_id", "")
        self.product_id: str = kwargs.get("product_id", "")
        self.quantity: int = kwargs.get("quantity", 1)
        self.is_substituted: bool = kwargs.get("is_substituted", False)


class UserPreference:
    """Stub UserPreference model matching design schema."""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", str(uuid4()))
        self.user_id: str = kwargs.get("user_id", "")
