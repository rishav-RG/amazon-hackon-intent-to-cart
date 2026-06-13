"""
Stub InventoryAdapter.

⚠️ Real implementation owned by another dev.
This stub defines the expected interface so Dev C's code can be imported.
"""


class InventoryAdapter:
    @staticmethod
    async def check_batch(product_ids: list[str]) -> list[dict]:
        """Check inventory for a batch of product IDs.

        Returns a list of dicts with keys: product_id, in_stock, substitutes.
        """
        raise NotImplementedError(
            "InventoryAdapter.check_batch() is a placeholder."
        )
