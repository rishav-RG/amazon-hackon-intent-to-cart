"""
Mock OrderAdapter for Intent-to-Cart backend.

Simulates order placement with external order management system.
In production, this would call an external OMS/fulfillment API.
"""

import asyncio
import uuid


class OrderAdapter:
    """
    Mock order adapter that simulates order placement with minimal delay.
    
    In production, this would integrate with an Order Management System
    to create orders, allocate inventory, and trigger fulfillment workflows.
    """
    
    @staticmethod
    async def place_order(user_id: str, items: list[dict]) -> dict:
        """
        Place an order for the given user with the specified items.
        
        Args:
            user_id: The user placing the order.
            items: List of order items, each dict with keys:
                   - product_id: str
                   - quantity: int
                   - unit_price: float
        
        Returns:
            Dictionary with order confirmation:
            {
                "order_id": "ORD-a1b2c3d4-...",
                "status": "confirmed",
                "user_id": "user-123",
                "total_items": 5
            }
            
        Note:
            - Simulates 50ms API latency
            - Always returns "confirmed" status in mock
            - Generates unique order ID with ORD- prefix
        """
        # Simulate network latency
        await asyncio.sleep(0.05)
        
        # Generate unique order ID
        order_id = f"ORD-{uuid.uuid4()}"
        
        return {
            "order_id": order_id,
            "status": "confirmed",
            "user_id": user_id,
            "total_items": len(items)
        }
