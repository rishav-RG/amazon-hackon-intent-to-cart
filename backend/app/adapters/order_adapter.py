"""
Stub OrderAdapter.

⚠️ Real implementation owned by another dev.
This stub defines the expected interface so Dev C's code can be imported.
"""


class OrderAdapter:
    @staticmethod
    async def place_order(user_id: str, items: list) -> dict:
        """Place an order for the given user with the given items.

        Returns a dict with at least: orderId, total.
        """
        raise NotImplementedError(
            "OrderAdapter.place_order() is a placeholder."
        )
