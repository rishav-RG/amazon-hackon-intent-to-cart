"""
RankingEngine for Intent-to-Cart backend.

Ranks bundles using a weighted multi-factor scoring algorithm.
Factors: intent match, inventory availability, ETA, personalization, completeness.
"""

from app.schemas.bundle import BundleSchema
from app.services.personalization_service import PersonalizationSignals
from app.config import settings


class RankingEngine:
    """
    Ranks bundles using weighted scoring across 5 factors.
    
    Scoring Formula:
        final_score = (
            w1 * intent_match_score +
            w2 * inventory_score +
            w3 * eta_score +
            w4 * personalization_score +
            w5 * completeness_score
        )
    
    Where weights (w1-w5) are from config and sum to 1.0.
    """
    
    @staticmethod
    def rank(
        bundles: list[BundleSchema],
        intent_type: str,
        signals: PersonalizationSignals
    ) -> list[BundleSchema]:
        """
        Rank bundles and return them sorted by score (highest first).
        
        Args:
            bundles: List of bundles to rank (must have inventory + ETA data).
            intent_type: The original intent type for intent matching.
            signals: Personalization signals for scoring.
            
        Returns:
            Bundles sorted by final_score descending (highest score first).
            Each bundle's final_score field is updated in-place.
            
        Note:
            - Bundles MUST have inventory/ETA data populated before ranking
            - Uses weights from config (RANKING_WEIGHT_* fields)
            - All scores normalized to 0.0-1.0 range
        """
        for bundle in bundles:
            # Calculate 5 factor scores
            intent_match = RankingEngine._score_intent_match(bundle, intent_type)
            inventory = RankingEngine._score_inventory(bundle)
            eta = RankingEngine._score_eta(bundle)
            personalization = RankingEngine._score_personalization(bundle, signals)
            completeness = RankingEngine._score_completeness(bundle)
            
            # Apply weighted formula
            final_score = (
                settings.RANKING_WEIGHT_INTENT_MATCH * intent_match +
                settings.RANKING_WEIGHT_INVENTORY * inventory +
                settings.RANKING_WEIGHT_ETA * eta +
                settings.RANKING_WEIGHT_PERSONALIZATION * personalization +
                settings.RANKING_WEIGHT_COMPLETENESS * completeness
            )
            
            # Update bundle in-place
            bundle.final_score = round(final_score, 4)
        
        # Sort descending by score
        return sorted(bundles, key=lambda b: b.final_score, reverse=True)
    
    @staticmethod
    def _score_intent_match(bundle: BundleSchema, intent_type: str) -> float:
        """
        Score how well bundle matches the intent.
        
        Perfect match (bundle.intent_type == intent_type): 1.0
        Mismatch: 0.5 (fallback bundles still have some value)
        """
        return 1.0 if bundle.intent_type == intent_type else 0.5
    
    @staticmethod
    def _score_inventory(bundle: BundleSchema) -> float:
        """
        Score based on inventory availability.
        
        Score = (available_items / total_items)
        
        Examples:
            - All items available: 1.0
            - 3/4 available: 0.75
            - All OOS: 0.0
        """
        total_items = len(bundle.items)
        if total_items == 0:
            return 0.0
        
        available_count = sum(
            1 for item in bundle.items 
            if not item.is_substituted and item.warehouse  # warehouse indicates availability
        )
        
        return available_count / total_items
    
    @staticmethod
    def _score_eta(bundle: BundleSchema) -> float:
        """
        Score based on delivery time (faster is better).
        
        Normalizes ETA to 0.0-1.0 range:
            - Fastest possible (20 min): 1.0
            - Slowest possible (90 min): 0.0
            - Linear scale in between
        
        Uses bundle's max ETA (slowest item determines delivery).
        """
        if not bundle.items:
            return 0.0
        
        # Get max ETA (slowest item)
        max_eta = max(item.eta_minutes for item in bundle.items)
        
        # Normalize using config min/max
        min_eta = settings.MOCK_ETA_MIN_MINUTES  # 20
        max_eta_config = settings.MOCK_ETA_MAX_MINUTES  # 90
        
        # Linear scale: faster = higher score
        if max_eta <= min_eta:
            return 1.0
        if max_eta >= max_eta_config:
            return 0.0
        
        # Linear interpolation
        score = 1.0 - ((max_eta - min_eta) / (max_eta_config - min_eta))
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _score_personalization(
        bundle: BundleSchema,
        signals: PersonalizationSignals
    ) -> float:
        """
        Score based on match with user preferences.
        
        Score = (matching_items / total_items)
        
        An item matches if:
            - Its brand is in preferred_brands, OR
            - Its category is in preferred_categories
        
        Examples:
            - All items match preferences: 1.0
            - 2/4 items match: 0.5
            - No matches: 0.0
        """
        total_items = len(bundle.items)
        if total_items == 0:
            return 0.0
        
        # Count items matching preferences
        matching_count = sum(
            1 for item in bundle.items
            if (item.brand in signals.preferred_brands or
                item.category in signals.preferred_categories)
        )
        
        return matching_count / total_items
    
    @staticmethod
    def _score_completeness(bundle: BundleSchema) -> float:
        """
        Score based on bundle completeness/diversity.
        
        Rewards bundles with:
            - More items (up to 6)
            - Higher total value
        
        Formula:
            item_score = min(item_count / 6, 1.0) * 0.6
            value_score = min(total_price / 50, 1.0) * 0.4
            completeness = item_score + value_score
        
        Examples:
            - 6 items, $50+: 1.0
            - 4 items, $30: ~0.64
            - 2 items, $10: ~0.28
        """
        item_count = len(bundle.items)
        total_price = bundle.total_price
        
        # Item diversity score (max at 6 items)
        item_score = min(item_count / 6.0, 1.0) * 0.6
        
        # Value score (max at $50)
        value_score = min(total_price / 50.0, 1.0) * 0.4
        
        return item_score + value_score
