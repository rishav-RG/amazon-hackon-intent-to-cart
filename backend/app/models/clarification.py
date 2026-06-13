"""
Clarification SQLAlchemy model.

Represents a clarification question/answer pair associated with an intent,
persisted to the 'clarifications' table.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.intent import Intent_Model


class Clarification_Model(Base):
    """SQLAlchemy model for the 'clarifications' table.

    Stores clarification questions posed to the user and their answers,
    linked to the parent intent via foreign key.
    """

    __tablename__ = "clarifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intents.id"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Many-to-one relationship: Clarification -> Intent
    intent: Mapped["Intent_Model"] = relationship(
        "Intent_Model",
        back_populates="clarifications",
    )
