"""
Intent SQLAlchemy model.

Represents a classified user intent persisted to the 'intents' table.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.clarification import Clarification_Model


class Intent_Model(Base):
    """SQLAlchemy model for the 'intents' table.

    Stores classified user intents with metadata including user/session IDs,
    raw text, classification result (type + confidence), and creation timestamp.
    """

    __tablename__ = "intents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # One-to-many relationship: Intent -> Clarifications
    clarifications: Mapped[list["Clarification_Model"]] = relationship(
        "Clarification_Model",
        back_populates="intent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
