"""
Product catalog adapter (mock implementation).
Developer B owns this file.

Returns product metadata for buy-again rail and other features.
"""


class ProductCatalogAdapter:
    """
    Returns product metadata from the mock catalog.
    
    Dev C's GET /v1/buy-again endpoint consumes this adapter.
    """

    async def get_products(self, product_ids: list[str]) -> list[dict]:
        """
        Get product metadata for a list of product IDs.
        
        Args:
            product_ids: List of product IDs to retrieve
            
        Returns:
            List of product dictionaries with fields:
            - product_id: str
            - name: str
            - brand: str
            - category: str
            - price: float
            - unit: str
            
        Notes:
            - Searches across all intent types in the mock catalog
            - Returns empty list if no products found
            - Order is not guaranteed to match input order
        """
        # Import here to avoid circular dependency
        # MOCK_CATALOG will be defined in bundle_generator.py (Phase 2)
        try:
            from app.services.bundle_generator import MOCK_CATALOG
        except ImportError:
            # Phase 1: bundle_generator doesn't exist yet
            # Return empty list for now
            return []

        # Flatten catalog across all intent types
        catalog_flat: dict[str, dict] = {}
        for products in MOCK_CATALOG.values():
            for p in products:
                catalog_flat[p["product_id"]] = p

        # Return products that match the requested IDs
        return [
            catalog_flat[pid]
            for pid in product_ids
            if pid in catalog_flat
        ]
