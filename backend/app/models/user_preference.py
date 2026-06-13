"""
Stub UserPreference ORM model.

⚠️ Dev A will provide the real implementation.
This stub defines the expected interface so Dev C's code can be imported.
"""
from sqlalchemy import Column, String
from app.models.cart import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, unique=True)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
