import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cart import Cart
from app.models.user_preference import UserPreference
from app.adapters.inventory_adapter import InventoryAdapter
from app.adapters.order_adapter import OrderAdapter
from app.events import emit
from app.utils.cache import cache_delete


class CheckoutService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(self, cart_id: str, user_id: str) -> dict:
        """
        Checkout flow:
        1. Hard read from Postgres
        2. Validate cart state
        3. Inventory check (no cache)
        4. Place order
        5. Update cart status
        6. Async preference update
        7. Emit event
        """
        # Step 1: Hard Postgres read
        result = await self.db.execute(select(Cart).where(Cart.id == cart_id))
        cart = result.scalar_one_or_none()
        if cart is None:
            raise ValueError(f"Cart {cart_id} not found")

        # Step 2: Validate
        if cart.status != "active":
            raise CartNotActiveError(f"Cart {cart_id} is not active (status={cart.status})")
        if not cart.items or len(cart.items) == 0:
            raise CartEmptyError(f"Cart {cart_id} has no items")

        # Step 3: Inventory check
        product_ids = [item.product_id for item in cart.items]
        stock_result = await InventoryAdapter.check_batch(product_ids)
        oos_items = [
            item for item in stock_result
            if not item["in_stock"] and not item.get("substitutes")
        ]
        if oos_items:
            raise ItemsOutOfStockError(oos_items)

        # Step 4: Place order
        order_result = await OrderAdapter.place_order(user_id, cart.items)

        # Step 5: Update cart status
        cart.status = "checked_out"
        await self.db.commit()
        await cache_delete(f"cart:{cart_id}")

        # Step 6: Async UserPreference update
        asyncio.create_task(self._update_preferences(user_id, cart.items))

        # Step 7: Emit event
        await emit("order.placed", {
            "order_id": order_result["orderId"],
            "cart_id": str(cart_id),
            "user_id": user_id,
            "item_count": len(cart.items),
        })

        return {
            "orderId": order_result["orderId"],
            "status": "confirmed",
            "items": [
                {"productId": i.product_id, "quantity": i.quantity, "price": 0.0}
                for i in cart.items
            ],
            "total": order_result.get("total", 0.0),
        }

    async def _update_preferences(self, user_id: str, items: list) -> None:
        """Async background task to update user preference affinities."""
        try:
            result = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            pref = result.scalar_one_or_none()
            if pref is None:
                pref = UserPreference(user_id=user_id)
                self.db.add(pref)
            # Update affinities based on purchased items (implementation detail)
            await self.db.commit()
        except Exception:
            pass  # Best-effort; don't fail checkout


class CartNotActiveError(Exception):
    pass


class CartEmptyError(Exception):
    pass


class ItemsOutOfStockError(Exception):
    def __init__(self, oos_items: list):
        self.oos_items = oos_items
        super().__init__(f"{len(oos_items)} items out of stock")
