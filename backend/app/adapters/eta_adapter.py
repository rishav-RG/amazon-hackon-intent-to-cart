"""
Mock ETAAdapter for Intent-to-Cart backend.

Simulates delivery time estimation with configurable range.
In production, this would call an external logistics/routing API.
"""

import random
from app.config import settings


class ETAAdapter:
    """
    Mock ETA adapter that generates random delivery time estimates.
    
    NOTE: No Redis caching in Phase 1. Cache integration happens in Phase 5
    when Dev C adds cache_get/cache_set calls (which Dev B reviews/approves).
    """
    
    @staticmethod
    async def get_batch(product_ids: list[str]) -> dict[str, dict]:
        """
        Get estimated delivery times for a batch of products.
        
        Args:
            product_ids: List of product IDs to estimate delivery for.
            
        Returns:
            Dictionary mapping product_id to ETA info:
            {
                "prod-001": {
                    "eta_minutes": 35,
                    "eta_label": "In 35 min"
                },
                "prod-002": {
                    "eta_minutes": 60,
                    "eta_label": "In 60 min"
                },
            }
            
        Note:
            - Uses MOCK_ETA_MIN_MINUTES and MOCK_ETA_MAX_MINUTES from config
            - Default range: 20-90 minutes
            - Empty input returns empty dict (no error)
        """
        result: dict[str, dict] = {}
        
        for product_id in product_ids:
            # Generate random ETA within configured range
            eta_minutes = random.randint(
                settings.MOCK_ETA_MIN_MINUTES,
                settings.MOCK_ETA_MAX_MINUTES
            )
            
            result[product_id] = {
                "eta_minutes": eta_minutes,
                "eta_label": f"In {eta_minutes} min"
            }
        
        return result
