"""
Stub Cart and CartItem ORM models.

⚠️ Dev A will provide the real implementation.
These stubs define the expected interface so Dev C's code can be imported.
"""
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Cart(Base):
    __tablename__ = "carts"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    bundle_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    version = Column(Integer, nullable=False, default=0)

    items = relationship("CartItem", back_populates="cart", lazy="selectin")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, "items") or self.items is None:
            self.items = []


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(String, primary_key=True)
    cart_id = Column(String, ForeignKey("carts.id"), nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    is_substituted = Column(Integer, nullable=False, default=0)  # boolean as int

    cart = relationship("Cart", back_populates="items")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, "is_substituted"):
            self.is_substituted = False
