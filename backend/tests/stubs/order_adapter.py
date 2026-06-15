"""
Stub OrderAdapter for tests.

Tests can override `OrderAdapter._response` to control place_order() output.
"""


class OrderAdapter:
    # Class-level configurable response.
    _response: dict | None = None

    @staticmethod
    async def place_order(user_id: str, items: list) -> dict:
        """Return configured order response or a default order confirmation."""
        if OrderAdapter._response is not None:
            return OrderAdapter._response
        return {"orderId": "order-test-001", "total": 99.99}

    @classmethod
    def reset(cls) -> None:
        """Reset to default behaviour."""
        cls._response = None
