"""
Personalization service - reads user preferences and returns personalization signals.
Developer B owns this file.
"""
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user_preference import UserPreference


@dataclass
class PersonalizationSignals:
    """
    Personalization signals extracted from user preferences.
    
    Attributes:
        preferred_brands: List of brands user prefers (sorted by affinity desc)
        preferred_categories: List of categories user prefers (sorted by affinity desc)
    """
    preferred_brands: list[str] = field(default_factory=list)
    preferred_categories: list[str] = field(default_factory=list)


class PersonalizationService:
    """
    Reads UserPreference for a user and returns brand/category signals.
    
    NOTE: No Redis caching here yet — Dev C adds cache_get/cache_set in Phase 5.
    Redis key pattern when Dev C integrates: personalization:{user_id} TTL=3600s
    """

    async def get_signals(
        self, user_id: str, db: AsyncSession
    ) -> PersonalizationSignals:
        """
        Returns PersonalizationSignals for the given user.
        
        If no UserPreference row exists, returns empty signals (safe default).
        This ensures bundle generation works even for new users.

        Args:
            user_id: The user's UUID string (or ID)
            db: Async SQLAlchemy session (injected by FastAPI dependency)

        Returns:
            PersonalizationSignals with preferred_brands and preferred_categories
            
        Notes:
            - brand_affinity is JSONB: {"Amul": 0.9, "Barilla": 0.7}
            - category_affinity is JSONB: {"pasta": 0.85, "dairy": 0.65}
            - Brands/categories are sorted by affinity weight descending
        """
        result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        pref = result.scalar_one_or_none()

        if pref is None:
            # New user or no preferences yet - return empty signals
            return PersonalizationSignals()

        # Extract brands sorted by affinity weight descending
        brand_affinity: dict = pref.brand_affinity or {}
        preferred_brands = [
            brand
            for brand, _ in sorted(
                brand_affinity.items(), key=lambda x: x[1], reverse=True
            )
        ]

        # Extract categories sorted by affinity weight descending
        category_affinity: dict = pref.category_affinity or {}
        preferred_categories = [
            cat
            for cat, _ in sorted(
                category_affinity.items(), key=lambda x: x[1], reverse=True
            )
        ]

        return PersonalizationSignals(
            preferred_brands=preferred_brands,
            preferred_categories=preferred_categories,
        )
