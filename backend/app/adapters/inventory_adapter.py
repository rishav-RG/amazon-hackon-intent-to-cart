"""
Inventory availability adapter (mock implementation).
Developer B owns this file.

In production, this would call an external warehouse API.
For development, it randomly marks products as out-of-stock based on config rate.
"""
import random
from app.config import get_settings

settings = get_settings()


class InventoryAdapter:
    """
    Mock inventory adapter for checking product availability.
    
    NOTE: No Redis caching yet. Cache integration is Phase 5 (Dev C's PR).
    Dev C will add cache_get/cache_set calls here; Dev B reviews and approves.
    """

    async def check_batch(self, product_ids: list[str]) -> dict[str, dict]:
        """
        Check availability for multiple products.
        
        Args:
            product_ids: List of product IDs to check
            
        Returns:
            Dictionary mapping product_id to availability info:
            {
                "prod-001": {"available": True,  "warehouse": "WH-A"},
                "prod-002": {"available": False, "warehouse": "WH-B"},
            }
            
        Notes:
            - Randomly marks products as OOS based on MOCK_INVENTORY_OOS_RATE
            - Each product gets a random warehouse assignment
            - This is deterministic within a single call but varies between calls
        """
        result: dict[str, dict] = {}
        warehouses = ["WH-A", "WH-B", "WH-C"]

        for product_id in product_ids:
            is_oos = random.random() < settings.MOCK_INVENTORY_OOS_RATE
            result[product_id] = {
                "available": not is_oos,
                "warehouse": random.choice(warehouses),
            }

        return result
