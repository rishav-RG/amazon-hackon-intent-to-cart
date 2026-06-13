"""
Bundle and BundleItem SQLAlchemy models.

Represents product bundles generated from classified intents,
stored in the 'bundles' and 'bundle_items' tables respectively.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from app.models.intent import Intent_Model


class Bundle_Model(Base):
    """SQLAlchemy model for the 'bundles' table.

    Stores product bundles produced from a classified intent, linking
    a user and intent to a named collection of bundle items.
    """

    __tablename__ = "bundles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intents.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # One-to-many relationship: Bundle -> BundleItems
    items: Mapped[list["BundleItem"]] = relationship(
        "BundleItem",
        back_populates="bundle",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class BundleItem(Base):
    """SQLAlchemy model for the 'bundle_items' table.

    Stores individual products within a bundle, including quantity and price.
    """

    __tablename__ = "bundle_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    bundle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bundles.id"),
        nullable=False,
    )
    product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Many-to-one relationship: BundleItem -> Bundle
    bundle: Mapped["Bundle_Model"] = relationship(
        "Bundle_Model",
        back_populates="items",
    )
