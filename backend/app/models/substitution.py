"""
Substitution SQLAlchemy model.

Represents a product substitution mapping — when one product can be replaced
by another, with an optional reason for the substitution.
"""

import uuid

from sqlalchemy import CheckConstraint, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Substitution_Model(Base):
    """SQLAlchemy model for the 'substitutions' table.

    Stores product substitution mappings with a unique constraint on the
    (original, replacement) pair and a check constraint preventing
    self-substitution.
    """

    __tablename__ = "substitutions"

    __table_args__ = (
        UniqueConstraint(
            "original_product_id",
            "replacement_product_id",
            name="uq_substitution_original_replacement",
        ),
        CheckConstraint(
            "original_product_id != replacement_product_id",
            name="ck_substitution_no_self_reference",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    original_product_id: Mapped[str] = mapped_column(String, nullable=False)
    replacement_product_id: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
