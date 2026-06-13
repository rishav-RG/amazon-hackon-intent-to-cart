"""
Stub InventoryAdapter for tests.

Tests can override `InventoryAdapter._response` to control check_batch() output.
"""


class InventoryAdapter:
    # Class-level configurable response.
    # Default: None means "generate default all-in-stock responses".
    _response: list[dict] | None = None

    @staticmethod
    async def check_batch(product_ids: list[str]) -> list[dict]:
        """Return configured inventory responses or default all-in-stock."""
        if InventoryAdapter._response is not None:
            return InventoryAdapter._response
        return [
            {"product_id": pid, "in_stock": True, "substitutes": []}
            for pid in product_ids
        ]

    @classmethod
    def reset(cls) -> None:
        """Reset to default behaviour."""
        cls._response = None
