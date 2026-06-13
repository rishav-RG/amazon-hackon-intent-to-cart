"""
Idempotent seed script for Cart & Checkout infrastructure.

Populates the database with sample Cart and CartItem records,
and pre-warms Redis cache keys for carts and buy-again data.

Usage:
    python seed.py
"""

import asyncio
import json
import sys

from app.database import get_db
from app.redis_client import get_redis
from app.models.cart import Cart, CartItem

# ---------------------------------------------------------------------------
# Sample Data
# ---------------------------------------------------------------------------

SAMPLE_CARTS = [
    {
        "id": "cart-001",
        "user_id": "user-100",
        "bundle_id": None,
        "status": "active",
        "version": 1,
        "items": [
            {
                "id": "item-001",
                "cart_id": "cart-001",
                "product_id": "prod-aaa",
                "quantity": 2,
                "is_substituted": 0,
            },
            {
                "id": "item-002",
                "cart_id": "cart-001",
                "product_id": "prod-bbb",
                "quantity": 1,
                "is_substituted": 0,
            },
        ],
    },
    {
        "id": "cart-002",
        "user_id": "user-100",
        "bundle_id": "bundle-x",
        "status": "checked_out",
        "version": 3,
        "items": [
            {
                "id": "item-003",
                "cart_id": "cart-002",
                "product_id": "prod-ccc",
                "quantity": 1,
                "is_substituted": 0,
            },
            {
                "id": "item-004",
                "cart_id": "cart-002",
                "product_id": "prod-ddd",
                "quantity": 4,
                "is_substituted": 1,
            },
        ],
    },
    {
        "id": "cart-003",
        "user_id": "user-200",
        "bundle_id": None,
        "status": "active",
        "version": 0,
        "items": [
            {
                "id": "item-005",
                "cart_id": "cart-003",
                "product_id": "prod-eee",
                "quantity": 3,
                "is_substituted": 0,
            },
        ],
    },
]

SAMPLE_BUY_AGAIN = {
    "user-100": [
        {
            "productId": "prod-ccc",
            "productName": "Wireless Mouse",
            "lastOrderedAt": "2025-01-15T10:30:00Z",
        },
        {
            "productId": "prod-ddd",
            "productName": "USB-C Hub",
            "lastOrderedAt": "2025-01-15T10:30:00Z",
        },
    ]
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CART_CACHE_TTL = 86400  # 24 hours
BUY_AGAIN_CACHE_TTL = 3600  # 1 hour


def _serialize_cart(cart_data: dict) -> dict:
    """Convert a cart dict to the JSON-serializable cache format."""
    return {
        "id": cart_data["id"],
        "userId": cart_data["user_id"],
        "bundleId": cart_data["bundle_id"],
        "status": cart_data["status"],
        "version": cart_data["version"],
        "items": [
            {
                "id": item["id"],
                "productId": item["product_id"],
                "quantity": item["quantity"],
                "isSubstituted": bool(item["is_substituted"]),
            }
            for item in cart_data["items"]
        ],
    }


# ---------------------------------------------------------------------------
# Database seeding (idempotent)
# ---------------------------------------------------------------------------


async def seed_database(session) -> None:
    """Insert sample carts and items into the database, skipping existing records."""
    from sqlalchemy import select

    for cart_data in SAMPLE_CARTS:
        # Check if cart already exists
        result = await session.execute(
            select(Cart).where(Cart.id == cart_data["id"])
        )
        existing_cart = result.scalars().first()

        if existing_cart is None:
            cart = Cart(
                id=cart_data["id"],
                user_id=cart_data["user_id"],
                bundle_id=cart_data["bundle_id"],
                status=cart_data["status"],
                version=cart_data["version"],
            )
            session.add(cart)
            print(f"  [DB] Inserted cart: {cart_data['id']} (status={cart_data['status']})")
        else:
            print(f"  [DB] Cart already exists, skipping: {cart_data['id']}")

        # Seed cart items
        for item_data in cart_data["items"]:
            result = await session.execute(
                select(CartItem).where(CartItem.id == item_data["id"])
            )
            existing_item = result.scalars().first()

            if existing_item is None:
                item = CartItem(
                    id=item_data["id"],
                    cart_id=item_data["cart_id"],
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    is_substituted=item_data["is_substituted"],
                )
                session.add(item)
                print(f"  [DB] Inserted cart item: {item_data['id']} (product={item_data['product_id']})")
            else:
                print(f"  [DB] Cart item already exists, skipping: {item_data['id']}")

    await session.commit()


# ---------------------------------------------------------------------------
# Redis cache seeding
# ---------------------------------------------------------------------------


async def seed_redis(redis) -> None:
    """Populate Redis cache keys for carts and buy-again data."""

    # Populate cart:{cartId} keys
    for cart_data in SAMPLE_CARTS:
        key = f"cart:{cart_data['id']}"
        value = json.dumps(_serialize_cart(cart_data))
        await redis.set(key, value, ex=CART_CACHE_TTL)
        print(f"  [Redis] Set {key} (TTL={CART_CACHE_TTL}s)")

    # Populate buy_again:{userId} keys
    for user_id, items in SAMPLE_BUY_AGAIN.items():
        key = f"buy_again:{user_id}"
        value = json.dumps(items)
        await redis.set(key, value, ex=BUY_AGAIN_CACHE_TTL)
        print(f"  [Redis] Set {key} (TTL={BUY_AGAIN_CACHE_TTL}s)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the seed script."""
    print("=" * 60)
    print("  Seed Script — Cart & Checkout Infrastructure")
    print("=" * 60)

    # --- Seed Database ---
    print("\n[1/2] Seeding database...")
    try:
        async for session in get_db():
            await seed_database(session)
        print("  [DB] Done.\n")
    except NotImplementedError:
        print("  [DB] WARNING: get_db() not implemented yet (placeholder).")
        print("  [DB] Skipping database seeding.\n")
    except Exception as exc:
        print(f"  [DB] ERROR: {exc}\n")
        sys.exit(1)

    # --- Seed Redis ---
    print("[2/2] Seeding Redis cache...")
    try:
        redis = await get_redis()
        await seed_redis(redis)
        print("  [Redis] Done.\n")
    except NotImplementedError:
        print("  [Redis] WARNING: get_redis() not implemented yet (placeholder).")
        print("  [Redis] Skipping Redis seeding.\n")
    except Exception as exc:
        print(f"  [Redis] ERROR: {exc}\n")
        sys.exit(1)

    print("=" * 60)
    print("  Seeding complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
