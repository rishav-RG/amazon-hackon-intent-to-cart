"""
Stub ProductCatalogAdapter for tests.

Tests can override `ProductCatalogAdapter._response` to control get_products() output.
"""


class ProductCatalogAdapter:
    # Class-level configurable response.
    _response: dict | None = None

    @staticmethod
    async def get_products(product_ids: list[str]) -> dict:
        """Return configured product metadata or generated defaults."""
        if ProductCatalogAdapter._response is not None:
            return ProductCatalogAdapter._response
        return {
            pid: {
                "name": f"Product {pid}",
                "lastOrderedAt": "2024-01-15T10:00:00Z",
            }
            for pid in product_ids
        }

    @classmethod
    def reset(cls) -> None:
        """Reset to default behaviour."""
        cls._response = None
