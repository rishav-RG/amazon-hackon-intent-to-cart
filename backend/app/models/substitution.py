"""
Substitution model stub - TEMPORARY
This stub enables Phase 3 development. Replace with Dev A's actual implementation when available.
"""
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Substitution(Base):
    """
    Product substitution mappings with confidence scores.
    
    When a product is out of stock, this table provides replacement options.
    Confidence >= 0.85 triggers auto-replacement.
    Confidence < 0.85 flags the item for user review.
    
    Table: substitutions
    """
    __tablename__ = "substitutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_product_id = Column(String, nullable=False, index=True)
    replacement_product_id = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0

    # NOTE: In production, Dev A should add:
    # - UNIQUE constraint on (original_product_id, replacement_product_id)
    # - created_at timestamp
    # - Index on original_product_id for fast lookups
