"""
Ranking engine - scores and sorts bundles by weighted formula.
Developer B owns this file.
"""
from app.schemas.bundle import BundleSchema
from app.services.personalization_service import PersonalizationSignals
from app.config import get_settings

settings = get_settings()


class RankingEngine:
    """
    Scores and sorts bundles by a weighted formula.
    Weights are loaded from config so they can be tuned without code changes.
    
    Formula:
        final_score = intent_match × 0.30
                    + inventory_score × 0.25
                    + eta_score × 0.15
                    + personalization_score × 0.20
                    + completeness × 0.10
    
    All individual scores are normalized to [0, 1] before weighting.
    """

    def rank(
        self,
        bundles: list[BundleSchema],
        intent_type: str,
        inventory_results: dict[str, dict],
        eta_results: dict[str, dict],
        signals: PersonalizationSignals,
    ) -> list[BundleSchema]:
        """
        Scores each bundle and returns them sorted by final_score descending.
        Mutates bundle.final_score in place.

        Args:
            bundles: The 3 BundleSchema objects from BundleGenerator
            intent_type: The original intent type string
            inventory_results: Output of InventoryAdapter.check_batch()
            eta_results: Output of ETAAdapter.get_batch()
            signals: PersonalizationSignals from PersonalizationService

        Returns:
            Bundles sorted by final_score descending (highest first)
            
        Notes:
            - All bundles' final_score field is updated in-place
            - Score range: 0.0 - 1.0
            - Higher score = better match for user
        """
        # Pre-compute the max ETA across all products for normalization
        all_eta = [
            v["eta_minutes"]
            for v in eta_results.values()
            if isinstance(v.get("eta_minutes"), (int, float))
        ]
        max_eta = max(all_eta) if all_eta else settings.MOCK_ETA_MAX_MINUTES

        for bundle in bundles:
            bundle.final_score = self._score(
                bundle, intent_type, inventory_results, eta_results, signals, max_eta
            )

        return sorted(bundles, key=lambda b: b.final_score, reverse=True)

    def _score(
        self,
        bundle: BundleSchema,
        intent_type: str,
        inventory_results: dict[str, dict],
        eta_results: dict[str, dict],
        signals: PersonalizationSignals,
        max_eta: float,
    ) -> float:
        """
        Calculate weighted score for a single bundle.
        
        Returns:
            Float score between 0.0 and 1.0
        """
        items = bundle.items
        if not items:
            return 0.0

        # 1. Intent match score (0–1): all items match the intent_type catalog
        # Here: 1.0 if the bundle's intent_type matches, else 0.5
        intent_score = 1.0 if bundle.intent_type == intent_type else 0.5

        # 2. Inventory score (0–1): fraction of items that are available
        available_count = sum(
            1
            for item in items
            if inventory_results.get(item.product_id, {}).get("available", True)
        )
        inventory_score = available_count / len(items)

        # 3. ETA score (0–1): lower ETA is better. Normalized as 1 - (avg_eta / max_eta)
        avg_eta = sum(
            eta_results.get(item.product_id, {}).get("eta_minutes", max_eta)
            for item in items
        ) / len(items)
        eta_score = 1.0 - (avg_eta / max_eta) if max_eta > 0 else 0.5

        # 4. Personalization score (0–1): fraction of items matching preferred brands/categories
        personalized_count = sum(
            1
            for item in items
            if item.brand in signals.preferred_brands
            or item.category in signals.preferred_categories
        )
        personalization_score = personalized_count / len(items)

        # 5. Completeness score (0–1): fraction of items not substituted / not OOS
        # All items present and not flagged = 1.0
        complete_count = sum(1 for item in items if not item.is_substituted)
        completeness_score = complete_count / len(items)

        # Weighted sum (weights from config)
        final_score = (
            intent_score        * settings.RANKING_WEIGHT_INTENT_MATCH
            + inventory_score   * settings.RANKING_WEIGHT_INVENTORY
            + eta_score         * settings.RANKING_WEIGHT_ETA
            + personalization_score * settings.RANKING_WEIGHT_PERSONALIZATION
            + completeness_score * settings.RANKING_WEIGHT_COMPLETENESS
        )

        return round(final_score, 6)
