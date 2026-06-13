"""
Order placement adapter (mock implementation).
Developer B owns this file.

In production, this would call an external order management system.
For development, it simulates order placement with a delay.
"""
import asyncio
import uuid


class OrderAdapter:
    """
    Mock order placement adapter.
    
    Simulates a 50ms external API call.
    Consumed by Dev C's CheckoutService - interface is frozen (Contract 5).
    """

    async def place_order(self, user_id: str, items: list[dict]) -> dict:
        """
        Place a mock order and return confirmation.
        
        Args:
            user_id: The authenticated user's ID
            items: List of order items, each with:
                   {"product_id": str, "quantity": int, ...}
                   
        Returns:
            Order confirmation:
            {"orderId": "ORD-a1b2c3d4", "status": "confirmed"}
            
        Notes:
            - Simulates 50ms external latency
            - Always succeeds (no validation in mock)
            - Order ID format: ORD-{first 8 chars of UUID}
        """
        # Simulate external API latency
        await asyncio.sleep(0.05)

        order_id = f"ORD-{str(uuid.uuid4())[:8]}"
        return {
            "orderId": order_id,
            "status": "confirmed",
        }
