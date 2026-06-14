from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cart import Cart_Model, CartItem
from app.utils.cache import cache_get, cache_set, cache_delete
from app.events import emit
from app.services.product_catalog import get_product_catalog

CART_CACHE_TTL = 86400  # 24 hours


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, bundle_id: Optional[str] = None) -> Cart_Model:
        """Create a new cart for the user."""
        cart = Cart_Model(user_id=user_id, bundle_id=bundle_id, status="active", version=0)
        self.db.add(cart)
        await self.db.commit()
        await self.db.refresh(cart)
        # Prime the cache
        await cache_set(f"cart:{cart.id}", self._serialize(cart), CART_CACHE_TTL)
        return cart

    async def get(self, cart_id: str) -> Optional[dict]:
        """Redis-first read, DB fallback."""
        cached = await cache_get(f"cart:{cart_id}")
        if cached is not None:
            return cached
        # DB fallback
        result = await self.db.execute(select(Cart_Model).where(Cart_Model.id == cart_id))
        cart = result.scalar_one_or_none()
        if cart is None:
            return None
        serialized = self._serialize(cart)
        await cache_set(f"cart:{cart_id}", serialized, CART_CACHE_TTL)
        return serialized

    async def get_by_user(self, user_id: str) -> Optional[Cart_Model]:
        """Get active cart for user from DB."""
        result = await self.db.execute(
            select(Cart_Model).where(Cart_Model.user_id == user_id, Cart_Model.status == "active")
        )
        return result.scalar_one_or_none()

    async def apply_operations(self, cart: Cart_Model, operations: list[dict]) -> Cart_Model:
        """Apply add/remove/update operations to a cart."""
        for op in operations:
            op_type = op["type"]
            if op_type == "add":
                await self._add_item(cart, op["productId"], op["quantity"])
            elif op_type == "remove":
                await self._remove_item(cart, op["productId"])
            elif op_type == "update":
                await self._update_item(cart, op["productId"], op["quantity"])
        return cart

    async def save(self, cart: Cart_Model) -> Cart_Model:
        """Persist cart: increment version, write to Redis (primary) + DB (write-through)."""
        cart.version += 1
        # Redis primary write
        await cache_set(f"cart:{cart.id}", self._serialize(cart), CART_CACHE_TTL)
        # DB write-through
        await self.db.commit()
        await self.db.refresh(cart)
        # Emit event
        await emit("cart.updated", {
            "cart_id": str(cart.id),
            "user_id": cart.user_id,
            "version": cart.version,
            "item_count": len(cart.items),
        })
        return cart

    def check_version(self, cart: Cart_Model, client_version: Optional[int]) -> bool:
        """Return True if version matches (or no version supplied)."""
        if client_version is None:
            return True
        return cart.version == client_version

    def _serialize(self, cart: Cart_Model) -> dict:
        """Convert cart ORM object to dict for caching."""
        return {
            "cartId": str(cart.id),
            "version": cart.version,
            "items": [
                {
                    "productId": item.product_id,
                    "productName": item.product_name,
                    "quantity": item.quantity,
                    "price": item.price,
                    **self._get_product_metadata(item.product_id),
                }
                for item in cart.items
            ],
            "total": sum(item.price * item.quantity for item in cart.items),
            "status": cart.status,
        }

    async def _add_item(self, cart: Cart_Model, product_id: str, quantity: int) -> None:
        """Add item to cart, resolving product_name and price from the catalog."""
        catalog = get_product_catalog()
        product = catalog.get_product_by_id(product_id)

        if product:
            product_name = product.get("name", "Unknown Product")
            # Prefer discount_price if available, fall back to price
            price = float(product.get("discount_price") or product.get("price", 0.01))
        else:
            product_name = f"Product {product_id}"
            price = 0.01  # Minimum allowed by DB constraint

        item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            price=price,
        )
        self.db.add(item)
        cart.items.append(item)

    def _get_product_metadata(self, product_id: str) -> dict:
        """Get additional product metadata (image, brand, category) from catalog."""
        catalog = get_product_catalog()
        product = catalog.get_product_by_id(product_id)
        if product:
            return {
                "imageUrl": product.get("image_url", ""),
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
                "unit": product.get("unit", ""),
            }
        return {"imageUrl": "", "brand": "", "category": "", "unit": ""}

    async def _remove_item(self, cart: Cart_Model, product_id: str) -> None:
        cart.items = [i for i in cart.items if i.product_id != product_id]
        await self.db.execute(
            CartItem.__table__.delete().where(
                CartItem.cart_id == cart.id, CartItem.product_id == product_id
            )
        )

    async def _update_item(self, cart: Cart_Model, product_id: str, quantity: int) -> None:
        for item in cart.items:
            if item.product_id == product_id:
                item.quantity = quantity
                break
