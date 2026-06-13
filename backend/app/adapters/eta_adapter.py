"""
ETA (Estimated Time of Arrival) adapter (mock implementation).
Developer B owns this file.

In production, this would call a logistics/delivery API.
For development, it generates random delivery times within config range.
"""
import random
from app.config import get_settings

settings = get_settings()


class ETAAdapter:
    """
    Mock ETA adapter for estimating product delivery times.
    
    NOTE: No Redis caching yet - Dev C adds that in Phase 5.
    """

    async def get_batch(
        self, product_ids: list[str], warehouse: str = "WH-A"
    ) -> dict[str, dict]:
        """
        Get delivery time estimates for multiple products.
        
        Args:
            product_ids: List of product IDs
            warehouse: Warehouse code (optional, affects ETA in production)
            
        Returns:
            Dictionary mapping product_id to ETA info:
            {
                "prod-001": {"eta_minutes": 35, "eta_label": "In 35 min"},
            }
            
        Notes:
            - Generates random ETA between MOCK_ETA_MIN_MINUTES and MOCK_ETA_MAX_MINUTES
            - Warehouse parameter accepted but not used in mock (for future use)
        """
        result: dict[str, dict] = {}

        for product_id in product_ids:
            eta_minutes = random.randint(
                settings.MOCK_ETA_MIN_MINUTES,
                settings.MOCK_ETA_MAX_MINUTES,
            )
            result[product_id] = {
                "eta_minutes": eta_minutes,
                "eta_label": f"In {eta_minutes} min",
            }

        return result
