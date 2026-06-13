"""
Mock InventoryAdapter for Intent-to-Cart backend.

Simulates warehouse inventory checks with configurable OOS rate.
In production, this would call an external warehouse management API.
"""

import random
from app.config import settings


class InventoryAdapter:
    """
    Mock inventory adapter that randomly marks products as out-of-stock.
    
    NOTE: No Redis caching in Phase 1. Cache integration happens in Phase 5
    when Dev C adds cache_get/cache_set calls (which Dev B reviews/approves).
    """
    
    @staticmethod
    async def check_batch(product_ids: list[str]) -> dict[str, dict]:
        """
        Check inventory availability for a batch of products.
        
        Args:
            product_ids: List of product IDs to check.
            
        Returns:
            Dictionary mapping product_id to availability info:
            {
                "prod-001": {"available": True, "warehouse": "WH-A"},
                "prod-002": {"available": False, "warehouse": "WH-B"},
            }
            
        Note:
            - Uses MOCK_INVENTORY_OOS_RATE from config (default 15%)
            - Randomly assigns one of three warehouses
            - Empty input returns empty dict (no error)
        """
        result: dict[str, dict] = {}
        warehouses = ["WH-A", "WH-B", "WH-C"]
        
        for product_id in product_ids:
            # Randomly mark product as OOS based on configured rate
            is_oos = random.random() < settings.MOCK_INVENTORY_OOS_RATE
            
            result[product_id] = {
                "available": not is_oos,
                "warehouse": random.choice(warehouses),
            }
        
        return result
