"""
UserPreference model stub - temporary until Dev A delivers.
"""
from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class UserPreference(Base):
    """
    User personalization preferences.
    Temporary stub - structure assumed based on CONTRACTS.md.
    """
    __tablename__ = "user_preferences"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_affinity = Column(JSON, nullable=True)  # {"BrandName": weight}
    category_affinity = Column(JSON, nullable=True)  # {"category": weight}
    reorder_frequency = Column(JSON, nullable=True)  # {"intent_type": days}
