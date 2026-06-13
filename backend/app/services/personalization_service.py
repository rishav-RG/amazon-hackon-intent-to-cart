"""
PersonalizationService for Intent-to-Cart backend.

Extracts user preference signals from UserPreference model for use in
bundle generation and ranking.
"""

from dataclasses import dataclass, field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_preference import UserPreference_Model


@dataclass
class PersonalizationSignals:
    """
    User preference signals extracted from UserPreference model.
    
    These signals are used by BundleGenerator to filter/prioritize products
    and by RankingEngine to boost bundle scores based on user preferences.
    """
    preferred_brands: list[str] = field(default_factory=list)
    preferred_categories: list[str] = field(default_factory=list)


class PersonalizationService:
    """
    Service for extracting personalization signals from user preference data.
    
    Reads UserPreference_Model and converts the JSONB dict fields into
    simple lists of preferred brands and categories (sorted by affinity score).
    """
    
    @staticmethod
    async def get_signals(user_id: str, db: AsyncSession) -> PersonalizationSignals:
        """
        Get personalization signals for a user.
        
        Args:
            user_id: The user ID to fetch preferences for.
            db: Async database session.
            
        Returns:
            PersonalizationSignals with preferred brands and categories.
            Returns empty lists if no preferences found for user.
            
        Note:
            - Reads from UserPreference_Model using CORRECT field names:
              * brand_preferences (NOT brand_affinity)
              * category_preferences (NOT category_affinity)
            - Sorts preferences by affinity score (highest first)
            - Only includes items with affinity >= 0.5
        """
        # Query user preferences
        result = await db.execute(
            select(UserPreference_Model).where(
                UserPreference_Model.user_id == user_id
            )
        )
        user_pref = result.scalar_one_or_none()
        
        # If no preferences exist, return empty signals
        if not user_pref:
            return PersonalizationSignals()
        
        # Extract and sort brand preferences (affinity >= 0.5)
        brand_prefs = user_pref.brand_preferences or {}
        preferred_brands = [
            brand for brand, affinity in 
            sorted(brand_prefs.items(), key=lambda x: x[1], reverse=True)
            if affinity >= 0.5
        ]
        
        # Extract and sort category preferences (affinity >= 0.5)
        category_prefs = user_pref.category_preferences or {}
        preferred_categories = [
            category for category, affinity in
            sorted(category_prefs.items(), key=lambda x: x[1], reverse=True)
            if affinity >= 0.5
        ]
        
        return PersonalizationSignals(
            preferred_brands=preferred_brands,
            preferred_categories=preferred_categories
        )
