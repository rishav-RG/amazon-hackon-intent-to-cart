# Design Document: Dev C — Cart, Checkout & Infrastructure

## Overview

This document describes the architecture, interfaces, and data flow for the Cart/Checkout infrastructure layer owned by Dev C. The system provides cart management (CRUD with optimistic locking), checkout orchestration (inventory verification → order placement → event emission), a buy-again rail, an in-process event bus, cache utilities, Pydantic schemas, stubs for external dependencies, and a seed script.

All code runs on FastAPI with asyncio. Redis is the primary read store for carts; PostgreSQL is the authoritative write store. The event bus is an in-process asyncio pub/sub — no external broker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                        │
├──────────────┬──────────────────┬────────────────────────────────┤
│ Cart Router  │ Checkout Router  │ Buy Again Router               │
│ PATCH /v1/cart│ POST /v1/checkout│ GET /v1/buy-again              │
│ GET /v1/cart/│                  │                                │
├──────────────┴──────────────────┴────────────────────────────────┤
│                       Service Layer                               │
│  ┌──────────────┐  ┌───────────────────┐                        │
│  │ Cart Service  │  │ Checkout Service   │                        │
│  └──────┬───────┘  └────────┬──────────┘                        │
│         │                    │                                    │
├─────────┼────────────────────┼────────────────────────────────────┤
│         │    Infrastructure   │                                    │
│  ┌──────▼───────┐  ┌────────▼────────┐  ┌────────────────────┐  │
│  │ Cache Utils   │  │ Event Bus        │  │ Schemas            │  │
│  └──────┬───────┘  └─────────────────┘  └────────────────────┘  │
│         │                                                         │
├─────────┼─────────────────────────────────────────────────────────┤
│         │        External Dependencies (NOT owned)                │
│  ┌──────▼───────┐  ┌────────────────┐  ┌─────────────────────┐  │
│  │ Redis Client  │  │ PostgreSQL/DB   │  │ Adapters (Inventory,│  │
│  │ (Dev A)       │  │ (Dev A)         │  │ Order, Catalog)     │  │
│  └──────────────┘  └────────────────┘  │ (Dev B)             │  │
│                                         └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components and Interfaces

### 1. Event Bus (`app/events.py`)

An in-process asyncio publish/subscribe system.

```python
from typing import Callable, Any
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

_subscribers: dict[str, list[Callable]] = {}


def subscribe(event_name: str, handler: Callable) -> None:
    """Register an async handler for the given event name."""
    if event_name not in _subscribers:
        _subscribers[event_name] = []
    _subscribers[event_name].append(handler)


async def emit(event_name: str, payload: dict) -> None:
    """Publish an event to all registered subscribers."""
    # Log the event to stdout in JSON format
    log_entry = json.dumps({"event": event_name, "payload": payload})
    print(log_entry, flush=True)

    handlers = _subscribers.get(event_name, [])
    results = await asyncio.gather(
        *(handler(payload) for handler in handlers),
        return_exceptions=True,
    )

    # Log exceptions from individual handlers but don't propagate
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(
                f"Handler {handlers[i].__name__} failed for event '{event_name}': {result}"
            )
```

**Key Decisions:**
- `asyncio.gather` with `return_exceptions=True` ensures exception isolation.
- JSON logging to stdout enables structured log aggregation.
- Module-level dict avoids instantiation ceremony — single bus per process.

---

### 2. Cache Utilities (`app/utils/cache.py`)

```python
import json
from typing import Optional

from app.redis_client import get_redis


async def cache_get(key: str) -> Optional[dict]:
    """Retrieve and JSON-deserialize a value from Redis."""
    try:
        redis = await get_redis()
        raw = await redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Cache read failed for key '{key}': {e}") from e


async def cache_set(key: str, value: dict, ttl: int) -> None:
    """JSON-serialize a value and store in Redis with TTL."""
    try:
        redis = await get_redis()
        await redis.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        raise RuntimeError(f"Cache write failed for key '{key}': {e}") from e


async def cache_delete(key: str) -> None:
    """Remove a key from Redis."""
    try:
        redis = await get_redis()
        await redis.delete(key)
    except Exception as e:
        raise RuntimeError(f"Cache delete failed for key '{key}': {e}") from e
```

**Key Decisions:**
- Wraps exceptions with context string for debuggability.
- Uses `RuntimeError` as placeholder; will align with Dev A's `AppException` once finalized.
- Every operation is try/except — cache failures propagate with context, never silently swallowed.

---

### 3. Pydantic Schemas

#### `app/schemas/cart.py`

```python
from __future__ import annotations
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class AddOperation(BaseModel):
    type: Literal["add"]
    productId: str
    quantity: int = Field(..., gt=0)


class RemoveOperation(BaseModel):
    type: Literal["remove"]
    productId: str


class UpdateOperation(BaseModel):
    type: Literal["update"]
    productId: str
    quantity: int = Field(..., gt=0)


CartOperation = Annotated[
    Union[AddOperation, RemoveOperation, UpdateOperation],
    Field(discriminator="type"),
]


class CartPatchRequest(BaseModel):
    operations: list[CartOperation]
    version: Optional[int] = Field(default=None, ge=0)


class CartItemResponse(BaseModel):
    productId: str
    quantity: int
    isSubstituted: bool = False


class CartResponse(BaseModel):
    cartId: str
    version: int
    items: list[CartItemResponse]
    total: float
    status: str
```

#### `app/schemas/checkout.py`

```python
from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    cartId: str


class CheckoutItemResponse(BaseModel):
    productId: str
    quantity: int
    price: float


class CheckoutResponse(BaseModel):
    orderId: str
    status: str  # "confirmed"
    items: list[CheckoutItemResponse]
    total: float


class OOSErrorDetail(BaseModel):
    productId: str
    availableQuantity: int
    substitutes: list[str]


class BuyAgainItem(BaseModel):
    productId: str
    productName: str
    lastOrderedAt: str
```

---

### 4. Cart Service (`app/services/cart_service.py`)

```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cart import Cart, CartItem
from app.utils.cache import cache_get, cache_set, cache_delete
from app.events import emit

CART_CACHE_TTL = 86400  # 24 hours


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, bundle_id: Optional[str] = None) -> Cart:
        """Create a new cart for the user."""
        cart = Cart(user_id=user_id, bundle_id=bundle_id, status="active", version=0)
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
        result = await self.db.execute(select(Cart).where(Cart.id == cart_id))
        cart = result.scalar_one_or_none()
        if cart is None:
            return None
        serialized = self._serialize(cart)
        await cache_set(f"cart:{cart_id}", serialized, CART_CACHE_TTL)
        return serialized

    async def get_by_user(self, user_id: str) -> Optional[Cart]:
        """Get active cart for user from DB."""
        result = await self.db.execute(
            select(Cart).where(Cart.user_id == user_id, Cart.status == "active")
        )
        return result.scalar_one_or_none()

    async def apply_operations(self, cart: Cart, operations: list[dict]) -> Cart:
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

    async def save(self, cart: Cart) -> Cart:
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

    def check_version(self, cart: Cart, client_version: Optional[int]) -> bool:
        """Return True if version matches (or no version supplied)."""
        if client_version is None:
            return True
        return cart.version == client_version

    def _serialize(self, cart: Cart) -> dict:
        """Convert cart ORM object to dict for caching."""
        return {
            "cartId": str(cart.id),
            "version": cart.version,
            "items": [
                {
                    "productId": item.product_id,
                    "quantity": item.quantity,
                    "isSubstituted": item.is_substituted,
                }
                for item in cart.items
            ],
            "total": sum(item.quantity for item in cart.items),  # placeholder
            "status": cart.status,
        }

    async def _add_item(self, cart: Cart, product_id: str, quantity: int) -> None:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        self.db.add(item)
        cart.items.append(item)

    async def _remove_item(self, cart: Cart, product_id: str) -> None:
        cart.items = [i for i in cart.items if i.product_id != product_id]
        await self.db.execute(
            CartItem.__table__.delete().where(
                CartItem.cart_id == cart.id, CartItem.product_id == product_id
            )
        )

    async def _update_item(self, cart: Cart, product_id: str, quantity: int) -> None:
        for item in cart.items:
            if item.product_id == product_id:
                item.quantity = quantity
                break
```

---

### 5. Checkout Service (`app/services/checkout_service.py`)

```python
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
```

---

### 6. Cart Router (`app/routers/cart.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.user import get_current_user_id
from app.services.cart_service import CartService
from app.schemas.cart import CartPatchRequest, CartResponse

router = APIRouter(prefix="/v1", tags=["cart"])


@router.patch("/cart", response_model=CartResponse)
async def patch_cart(
    body: CartPatchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart = await service.get_by_user(user_id)
    if cart is None:
        cart = await service.create(user_id)

    # Optimistic lock check
    if not service.check_version(cart, body.version):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Version conflict",
                "serverVersion": cart.version,
                "cart": service._serialize(cart),
            },
        )

    # Apply operations
    operations = [op.model_dump() for op in body.operations]
    cart = await service.apply_operations(cart, operations)
    cart = await service.save(cart)

    return service._serialize(cart)


@router.get("/cart/{cart_id}", response_model=CartResponse)
async def get_cart(
    cart_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart_data = await service.get(cart_id)
    if cart_data is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart_data
```

---

### 7. Checkout Router (`app/routers/checkout.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.user import get_current_user_id
from app.services.checkout_service import (
    CheckoutService,
    CartNotActiveError,
    CartEmptyError,
    ItemsOutOfStockError,
)
from app.schemas.checkout import CheckoutRequest, CheckoutResponse

router = APIRouter(prefix="/v1", tags=["checkout"])


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CheckoutService(db)
    try:
        result = await service.execute(body.cartId, user_id)
        return result
    except CartNotActiveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CartEmptyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ItemsOutOfStockError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ITEMS_OUT_OF_STOCK",
                "items": e.oos_items,
            },
        )
```

---

### 8. Buy Again Router (`app/routers/buy_again.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.user import get_current_user_id
from app.utils.cache import cache_get, cache_set
from app.models.cart import Cart, CartItem
from app.adapters.catalog_adapter import ProductCatalogAdapter
from app.schemas.checkout import BuyAgainItem

router = APIRouter(prefix="/v1", tags=["buy-again"])

BUY_AGAIN_TTL = 3600  # 1 hour


@router.get("/buy-again", response_model=list[BuyAgainItem])
async def buy_again(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"buy_again:{user_id}"

    # Cache-first
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    # DB fallback: Cart join CartItem for checked-out carts
    result = await db.execute(
        select(CartItem)
        .join(Cart, CartItem.cart_id == Cart.id)
        .where(Cart.user_id == user_id, Cart.status == "checked_out")
    )
    items = result.scalars().all()

    if not items:
        return []

    # Enrich via ProductCatalogAdapter
    product_ids = list({item.product_id for item in items})
    catalog_data = await ProductCatalogAdapter.get_products(product_ids)

    buy_again_items = [
        {
            "productId": pid,
            "productName": catalog_data.get(pid, {}).get("name", "Unknown"),
            "lastOrderedAt": catalog_data.get(pid, {}).get("lastOrderedAt", ""),
        }
        for pid in product_ids
    ]

    # Populate cache before returning
    await cache_set(cache_key, buy_again_items, BUY_AGAIN_TTL)

    return buy_again_items
```

---

### 9. Seed Script (`backend/seed.py`)

```python
"""
Idempotent seed script for local development.
Run: python seed.py (from backend directory)
"""
import asyncio
import json
from app.database import get_db
from app.redis_client import get_redis
from app.models.cart import Cart, CartItem

SAMPLE_CARTS = [
    {
        "id": "cart-seed-001",
        "user_id": "user-seed-001",
        "status": "active",
        "version": 1,
        "items": [
            {"product_id": "prod-001", "quantity": 2},
            {"product_id": "prod-002", "quantity": 1},
        ],
    },
    {
        "id": "cart-seed-002",
        "user_id": "user-seed-001",
        "status": "checked_out",
        "version": 3,
        "items": [
            {"product_id": "prod-003", "quantity": 1},
        ],
    },
]


async def seed():
    async for db in get_db():
        for cart_data in SAMPLE_CARTS:
            # Upsert cart (idempotent)
            existing = await db.get(Cart, cart_data["id"])
            if existing is None:
                cart = Cart(
                    id=cart_data["id"],
                    user_id=cart_data["user_id"],
                    status=cart_data["status"],
                    version=cart_data["version"],
                )
                db.add(cart)
                await db.flush()
                for item in cart_data["items"]:
                    db.add(CartItem(
                        cart_id=cart_data["id"],
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                    ))
            await db.commit()

        # Populate Redis cache
        redis = await get_redis()
        for cart_data in SAMPLE_CARTS:
            cache_value = json.dumps({
                "cartId": cart_data["id"],
                "version": cart_data["version"],
                "items": [
                    {"productId": i["product_id"], "quantity": i["quantity"], "isSubstituted": False}
                    for i in cart_data["items"]
                ],
                "total": sum(i["quantity"] for i in cart_data["items"]),
                "status": cart_data["status"],
            })
            await redis.set(f"cart:{cart_data['id']}", cache_value, ex=86400)

        # Populate buy_again cache
        buy_again_data = json.dumps([
            {"productId": "prod-003", "productName": "Sample Product", "lastOrderedAt": "2024-01-15T10:00:00Z"}
        ])
        await redis.set("buy_again:user-seed-001", buy_again_data, ex=3600)

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
```

---

### 10. Stub/Mock Layer (`tests/stubs/`)

All stubs reside in `tests/stubs/`. Dev C does NOT create files in `app/models/`.

| File | Purpose |
|------|---------|
| `tests/stubs/redis_client.py` | In-memory dict implementing async get/set/delete |
| `tests/stubs/database.py` | Async session factory returning mock or SQLite-backed session |
| `tests/stubs/models.py` | Stub Cart, CartItem, UserPreference with expected columns |
| `tests/stubs/inventory_adapter.py` | Configurable `check_batch()` returning stock/substitute data |
| `tests/stubs/order_adapter.py` | `place_order()` returning generated order_id |
| `tests/stubs/catalog_adapter.py` | `get_products()` returning product metadata dicts |

---

## Data Models

Dev C reads/writes these tables but does NOT own their definitions (Dev A owns `app/models/`):

```
Cart
├── id: UUID (PK)
├── user_id: str
├── bundle_id: str (nullable)
├── status: str (enum: active, checked_out)
├── version: int
└── updated_at: datetime

CartItem
├── id: UUID (PK)
├── cart_id: UUID (FK → Cart.id)
├── product_id: str
├── quantity: int
└── is_substituted: bool

UserPreference
├── user_id: str (PK)
├── brand_affinity: JSONB
├── category_affinity: JSONB
├── reorder_frequency: JSONB
└── last_updated_at: datetime
```

---

## Redis Key Patterns

| Key Pattern | TTL | Owner | Description |
|-------------|-----|-------|-------------|
| `cart:{cartId}` | 86400s (24h) | CartService | JSON-serialized cart state |
| `buy_again:{userId}` | 3600s (1h) | BuyAgainRouter | JSON array of BuyAgainItem |

---

## Error Handling

| Scenario | HTTP Code | Error Code | Response Body |
|----------|-----------|------------|---------------|
| Version conflict on PATCH /v1/cart | 409 | — | `{ message, serverVersion, cart }` |
| Cart not found | 404 | — | `{ detail: "Cart not found" }` |
| Cart not active (checkout) | 400 | — | `{ detail: "Cart {id} is not active" }` |
| Cart empty (checkout) | 400 | — | `{ detail: "Cart {id} has no items" }` |
| Items out of stock | 422 | ITEMS_OUT_OF_STOCK | `{ code, items: [...] }` |
| Redis unreachable (cache) | 500 | — | RuntimeError with context (re-raised) |

---

## Events Emitted

| Event Name | Payload | Emitter |
|------------|---------|---------|
| `cart.updated` | `{ cart_id, user_id, version, item_count }` | CartService.save() |
| `order.placed` | `{ order_id, cart_id, user_id, item_count }` | CheckoutService.execute() |

---

## Dependencies (Imports from Other Devs)

| Import | Source | Owner |
|--------|--------|-------|
| `app.database.get_db` | AsyncSession factory | Dev A |
| `app.redis_client.get_redis` | Redis connection | Dev A |
| `app.models.cart.Cart` | ORM model | Dev A |
| `app.models.cart.CartItem` | ORM model | Dev A |
| `app.models.user_preference.UserPreference` | ORM model | Dev A |
| `app.utils.exceptions.AppException` | Base exception | Dev A |
| `app.utils.user.get_current_user_id` | FastAPI dependency | Dev A |
| `app.adapters.inventory_adapter.InventoryAdapter` | Inventory check | Dev B |
| `app.adapters.order_adapter.OrderAdapter` | Order placement | Dev B |
| `app.adapters.catalog_adapter.ProductCatalogAdapter` | Product metadata | Dev B |

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Event delivery to all subscribers

*For any* event name and *for any* set of N registered handlers (N ≥ 0), when `emit(event_name, payload)` is called, all N handlers shall be invoked exactly once with the given payload.

**Validates: Requirements 1.1, 1.3**

### Property 2: Event emission produces valid JSON log

*For any* event name (non-empty string) and *for any* payload (valid dict), calling `emit` shall produce exactly one line on stdout that is valid JSON containing both the event name and payload.

**Validates: Requirements 1.2**

### Property 3: Exception isolation in event handlers

*For any* set of N handlers where K handlers (0 ≤ K ≤ N) raise exceptions, all (N - K) non-throwing handlers shall still be invoked and complete successfully.

**Validates: Requirements 1.5**

### Property 4: Cache set/get round-trip

*For any* key (non-empty string) and *for any* value (JSON-serializable dict), `cache_set(key, value, ttl)` followed by `cache_get(key)` shall return a value equal to the original value.

**Validates: Requirements 2.1, 2.2**

### Property 5: Cache delete removes entry

*For any* key that has been previously set via `cache_set`, calling `cache_delete(key)` followed by `cache_get(key)` shall return None.

**Validates: Requirements 2.3**

### Property 6: Cart operation version increment

*For any* cart with version V and *for any* valid operation (add, remove, or update), applying the operation and saving shall produce a cart with version V + 1.

**Validates: Requirements 3.2, 3.3, 3.4**

### Property 7: Cart creation for new users

*For any* user_id that has no existing active cart, when a PATCH request with operations arrives, a new cart shall be created with version 0 before operations are applied, and the final cart shall have version 1.

**Validates: Requirements 3.1**

### Property 8: Cart mutation event emission

*For any* successful cart mutation (add, remove, or update), a `cart.updated` event shall be emitted with a payload containing the correct cart_id, user_id, version, and item_count values matching the post-mutation cart state.

**Validates: Requirements 3.5**

### Property 9: Optimistic lock rejection on version mismatch

*For any* cart with server version V and *for any* client-supplied version C where C ≠ V, the PATCH request shall be rejected with HTTP 409, and the response body shall include the current server version V and the full current cart state.

**Validates: Requirements 3.6**

### Property 10: Checkout validation rejects invalid carts

*For any* cart where status ≠ "active" OR item count = 0, the checkout service shall reject the request with HTTP 400 without calling InventoryAdapter or OrderAdapter.

**Validates: Requirements 5.2, 5.3, 5.4**

### Property 11: OOS items correctly reported

*For any* cart containing items and *for any* inventory state where a subset S (|S| ≥ 1) of items are out-of-stock with no substitution available, the checkout response shall have HTTP 422 with error code `ITEMS_OUT_OF_STOCK` and the response body shall list exactly the items in S.

**Validates: Requirements 5.6**

### Property 12: Successful checkout transitions cart status

*For any* valid cart (active, ≥1 item, all in stock) that completes checkout successfully, the cart status in the database shall be updated to "checked_out".

**Validates: Requirements 5.8**

### Property 13: Order placed event emission

*For any* successful checkout, an `order.placed` event shall be emitted with payload containing orderId, cartId, userId, and itemCount where itemCount equals the number of items in the checked-out cart.

**Validates: Requirements 5.10**

### Property 14: Checkout response contains required fields

*For any* successful checkout, the HTTP 200 response shall contain orderId (non-empty string), status equal to "confirmed", items (list), and total (number ≥ 0).

**Validates: Requirements 6.2**

### Property 15: Buy-again cache population after DB fallback

*For any* user with checked-out carts but no `buy_again:{userId}` cache entry, calling GET /v1/buy-again shall populate the Redis cache key `buy_again:{userId}` with TTL 3600s, such that a subsequent call returns the cached data without querying the database.

**Validates: Requirements 7.5**

### Property 16: Schema quantity validation rejects non-positive values

*For any* integer quantity ≤ 0, constructing an AddOperation or UpdateOperation with that quantity shall raise a Pydantic ValidationError.

**Validates: Requirements 8.8**

### Property 17: Schema version validation rejects negative values

*For any* integer version < 0, constructing a CartPatchRequest with that version shall raise a Pydantic ValidationError. Values ≥ 0 shall be accepted.

**Validates: Requirements 8.9**

### Property 18: Mock Redis round-trip

*For any* key and *for any* JSON-serializable value, the stub redis_client's set followed by get shall return the same value, and delete followed by get shall return None.

**Validates: Requirements 9.3**

### Property 19: Seed script idempotence

*For any* initial database state, running the seed script twice in succession shall produce the same final state as running it once — no duplicate records, no version drift, and identical Redis cache contents.

**Validates: Requirements 10.2**

---

## Testing Strategy

### Test Framework

- **pytest** 9.0.3 with **pytest-asyncio** 1.4.0
- Property-based testing via **hypothesis** (to be added to requirements.txt)
- All stubs in `tests/stubs/` — never in production code paths

### Test Organization

```
tests/
├── stubs/
│   ├── redis_client.py
│   ├── database.py
│   ├── models.py
│   ├── inventory_adapter.py
│   ├── order_adapter.py
│   └── catalog_adapter.py
├── unit/
│   ├── test_events.py
│   ├── test_cache.py
│   ├── test_cart_service.py
│   ├── test_checkout_service.py
│   └── test_schemas.py
├── integration/
│   ├── test_cart_router.py
│   ├── test_checkout_router.py
│   └── test_buy_again_router.py
└── test_seed.py
```

### Property Test Configuration

- Minimum 100 iterations per property
- Each property test references its design property by number
- Tag format: `Feature: dev-c-cart-checkout-infrastructure, Property {N}: {title}`
