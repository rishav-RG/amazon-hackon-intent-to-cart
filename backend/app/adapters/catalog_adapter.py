"""
Stub ProductCatalogAdapter.

⚠️ Real implementation owned by another dev.
This stub defines the expected interface so Dev C's code can be imported.
"""


class ProductCatalogAdapter:
    @staticmethod
    async def get_products(product_ids: list[str]) -> dict:
        """Fetch product metadata for the given product IDs.

        Returns a dict mapping product_id -> { name, lastOrderedAt, ... }.
        """
        raise NotImplementedError(
            "ProductCatalogAdapter.get_products() is a placeholder."
        )
