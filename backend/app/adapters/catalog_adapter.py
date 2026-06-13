"""
Mock ProductCatalogAdapter for Intent-to-Cart backend.

Provides product metadata lookups from mock catalog.
In production, this would call an external product information management API.
"""


class ProductCatalogAdapter:
    """
    Mock product catalog adapter that returns product metadata.
    
    In Phase 1, this returns a minimal implementation. The full 48-product
    MOCK_CATALOG will be created in bundle_generator.py (Phase 2), and this
    adapter will reference it.
    
    For now, this provides the interface contract that other services expect.
    """
    
    @staticmethod
    async def get_products(product_ids: list[str]) -> list[dict]:
        """
        Fetch product metadata for the given product IDs.
        
        Args:
            product_ids: List of product IDs to fetch.
            
        Returns:
            List of product dictionaries, each containing:
            {
                "product_id": str,
                "name": str,
                "brand": str,
                "category": str,
                "price": float,
                "unit": str
            }
            
        Note:
            - Phase 1: Returns empty list (catalog defined in Phase 2)
            - Phase 2: Will reference MOCK_CATALOG from bundle_generator
            - Production: Would call external PIM API
        """
        # Phase 1: Minimal implementation
        # Full catalog integration happens in Phase 2
        return []
