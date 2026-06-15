# Implementation Plan: Dev C — Cart, Checkout & Infrastructure

## Overview

Hackathon-speed implementation plan for the Cart/Checkout infrastructure layer. 8 phases, linear dependency order, no property-based tests. All tasks are required. Testing uses pytest + pytest-asyncio with focused unit and integration tests.

**Language:** Python (FastAPI, Pydantic v2, SQLAlchemy async, Redis)

## Tasks

- [x] 1. Event Bus and Cache Utilities
  - [x] 1.1 Implement `app/events.py` — in-process asyncio pub/sub event bus
    - Create module-level `_subscribers` dict
    - Implement `subscribe(event_name, handler)` to register async handlers
    - Implement `emit(event_name, payload)` using `asyncio.gather(return_exceptions=True)`
    - Log events to stdout in JSON format
    - Log handler exceptions without propagating
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.2 Implement `app/utils/cache.py` — Redis cache wrapper
    - Implement `cache_get(key)` → JSON-deserialize from Redis, return None on miss
    - Implement `cache_set(key, value, ttl)` → JSON-serialize and store with TTL
    - Implement `cache_delete(key)` → remove key from Redis
    - Wrap all operations in try/except, re-raise as RuntimeError with context
    - **⚠️ Note:** Import `from app.redis_client import get_redis` — exact function signature pending confirmation from Dev A. Ask Dev A for final API before implementing.
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Pydantic Schemas
  - [x] 2.1 Implement `app/schemas/cart.py`
    - Define `AddOperation`, `RemoveOperation`, `UpdateOperation` with `type` discriminator
    - Define `CartOperation` as annotated discriminated union
    - Define `CartPatchRequest` with `operations` list and optional `version` (ge=0)
    - Define `CartItemResponse` and `CartResponse`
    - Add field validators: quantity > 0, version >= 0
    - _Requirements: 8.1, 8.2, 8.3, 8.8, 8.9_

  - [x] 2.2 Implement `app/schemas/checkout.py`
    - Define `CheckoutRequest` (cartId)
    - Define `CheckoutItemResponse` (productId, quantity, price)
    - Define `CheckoutResponse` (orderId, status, items, total)
    - Define `OOSErrorDetail` (productId, availableQuantity, substitutes)
    - Define `BuyAgainItem` (productId, productName, lastOrderedAt)
    - _Requirements: 8.4, 8.5, 8.6, 8.7_

- [x] 3. Cart Service
  - [x] 3.1 Implement `app/services/cart_service.py`
    - Define `CartService` class accepting `AsyncSession`
    - Implement `create(user_id, bundle_id=None)` → new cart with status="active"
    - **⚠️ Note:** Initial cart version (0 vs 1) needs confirmation from Dev A. Using `version=0` as default — verify with Dev A before finalizing.
    - Implement `get(cart_id)` → Redis-first read with DB fallback
    - Implement `get_by_user(user_id)` → DB query for active cart
    - Implement `apply_operations(cart, operations)` → dispatch add/remove/update
    - Implement `save(cart)` → increment version, write Redis + DB, emit `cart.updated` event
    - Implement `check_version(cart, client_version)` → optimistic lock check
    - Implement `_serialize(cart)` → dict for cache/response
    - Implement `_add_item`, `_remove_item`, `_update_item` private methods
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4. Cart Router
  - [x] 4.1 Implement `app/routers/cart.py`
    - Define FastAPI `APIRouter` with prefix `/v1`
    - Implement `PATCH /cart` endpoint:
      - Inject `user_id` via `get_current_user_id` dependency
      - Get or create cart for user
      - Check optimistic lock version → 409 on mismatch
      - Apply operations and save
      - Return `CartResponse`
    - Implement `GET /cart/{cart_id}` endpoint:
      - Delegate to `CartService.get()`
      - Return 404 if not found
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Checkpoint — Cart layer complete
  - Ensure cart service and router are wired correctly.
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Checkout Service
  - [x] 6.1 Implement `app/services/checkout_service.py`
    - Define `CheckoutService` class accepting `AsyncSession`
    - Implement `execute(cart_id, user_id)` with 7-step flow:
      1. Hard Postgres read (no cache)
      2. Validate cart status == "active" and items > 0
      3. Call `InventoryAdapter.check_batch()` for stock check
      4. Call `OrderAdapter.place_order()` on success
      5. Update cart status to "checked_out", delete cache
      6. Fire-and-forget `_update_preferences()` via `asyncio.create_task`
      7. Emit `order.placed` event
    - Define exception classes: `CartNotActiveError`, `CartEmptyError`, `ItemsOutOfStockError`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10_

- [x] 7. Checkout and Buy-Again Routers
  - [x] 7.1 Implement `app/routers/checkout.py`
    - Define FastAPI `APIRouter` with prefix `/v1`
    - Implement `POST /checkout` endpoint:
      - Accept `CheckoutRequest` body
      - Delegate to `CheckoutService.execute()`
      - Map exceptions: `CartNotActiveError` → 400, `CartEmptyError` → 400, `ItemsOutOfStockError` → 422
      - Return `CheckoutResponse` on success
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 7.2 Implement `app/routers/buy_again.py`
    - Define FastAPI `APIRouter` with prefix `/v1`
    - Implement `GET /buy-again` endpoint:
      - Identify user via `get_current_user_id` dependency
      - Cache-first: read `buy_again:{userId}` from Redis (TTL 3600s)
      - DB fallback: query Cart+CartItem for checked-out carts
      - Enrich via `ProductCatalogAdapter.get_products()`
      - Populate cache before returning
      - Return `list[BuyAgainItem]`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Checkpoint — All services and routers complete
  - Ensure checkout and buy-again routers are wired correctly.
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Stubs and Tests
  - [x] 9.1 Create `tests/stubs/redis_client.py` — in-memory dict mock
    - Implement async `get(key)`, `set(key, value, ex=None)`, `delete(key)` operating on a dict
    - Expose a `get_redis()` async function returning the mock instance
    - _Requirements: 9.1, 9.3_

  - [x] 9.2 Create `tests/stubs/database.py` — async session mock
    - Provide async session factory returning a functional AsyncSession (SQLite in-memory or mock)
    - _Requirements: 9.1, 9.5_

  - [x] 9.3 Create `tests/stubs/models.py` — stub ORM models
    - Define stub `Cart`, `CartItem`, `UserPreference` with expected columns
    - Match schema from design document (id, user_id, status, version, items, etc.)
    - _Requirements: 9.1, 9.2, 9.4_

  - [x] 9.4 Create `tests/stubs/inventory_adapter.py`, `tests/stubs/order_adapter.py`, `tests/stubs/catalog_adapter.py`
    - `InventoryAdapter.check_batch()` → configurable stock/substitute responses
    - `OrderAdapter.place_order()` → return generated order_id
    - `ProductCatalogAdapter.get_products()` → return product metadata dicts
    - _Requirements: 9.6, 9.7, 9.8_

  - [x] 9.5 Create `tests/test_events.py` — unit tests for event bus
    - Test: emit calls all registered handlers with correct payload
    - Test: emit with zero subscribers does not raise
    - Test: handler exception does not crash other handlers
    - Test: JSON log output on emit
    - Test: subscribe multiple handlers to same event
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 9.6 Create `tests/test_cache.py` — unit tests for cache utilities
    - Test: cache_set then cache_get returns original value
    - Test: cache_get on missing key returns None
    - Test: cache_delete removes the key
    - Test: Redis error propagates as RuntimeError with context
    - Use `tests/stubs/redis_client.py` mock
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 9.7 Create `tests/test_cart_service.py` — unit tests for cart service
    - Test: create() initializes cart with correct user_id and version
    - Test: get() returns from cache when available
    - Test: get() falls back to DB when cache misses
    - Test: apply_operations add/remove/update mutate cart correctly
    - Test: save() increments version and emits cart.updated event
    - Test: check_version rejects mismatched versions
    - Use stubs for DB session, Redis, and models
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 9.8 Create `tests/test_checkout_service.py` — unit tests for checkout service
    - Test: rejects cart with status != "active" (400)
    - Test: rejects empty cart (400)
    - Test: returns 422 with OOS items when inventory fails
    - Test: successful checkout updates cart status to "checked_out"
    - Test: successful checkout emits order.placed event
    - Test: successful checkout deletes cart cache
    - Use stubs for DB, InventoryAdapter, OrderAdapter
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.10_

  - [x] 9.9 Create `tests/test_cart_router.py` — integration tests for cart endpoints
    - Test: PATCH /v1/cart with add operation → 200 with updated cart
    - Test: PATCH /v1/cart with version conflict → 409
    - Test: PATCH /v1/cart for new user creates cart automatically
    - Test: GET /v1/cart/{cartId} returns cart state
    - Test: GET /v1/cart/{cartId} for non-existent cart → 404
    - Use `httpx.AsyncClient` with FastAPI TestClient
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 9.10 Create `tests/test_checkout_router.py` — integration tests for checkout endpoint
    - Test: POST /v1/checkout with valid cart → 200 confirmed
    - Test: POST /v1/checkout with inactive cart → 400
    - Test: POST /v1/checkout with OOS items → 422
    - Use `httpx.AsyncClient` with FastAPI TestClient
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 9.11 Create `tests/test_buy_again_router.py` — integration tests for buy-again endpoint
    - Test: GET /v1/buy-again returns cached data when available
    - Test: GET /v1/buy-again falls back to DB and populates cache
    - Test: GET /v1/buy-again returns empty list for user with no orders
    - Use `httpx.AsyncClient` with FastAPI TestClient
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 10. Checkpoint — All tests passing
  - Ensure all tests pass, ask the user if questions arise.
  - Testing framework: pytest==9.0.3, pytest-asyncio==1.4.0 (NO hypothesis)

- [x] 11. Seed Script
  - [x] 11.1 Implement `backend/seed.py` — idempotent seed script
    - Import from `app.database.get_db` and `app.redis_client.get_redis`
    - Define sample cart data (active + checked_out carts with items)
    - Upsert carts and cart items into DB (skip if already exists)
    - Populate Redis `cart:{cartId}` keys with TTL 86400s
    - Populate Redis `buy_again:{userId}` key with TTL 3600s
    - Make script runnable via `python seed.py` from backend directory
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 12. Final Checkpoint
  - Ensure all tests pass and seed script runs without errors.
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- **No property-based tests** — hackathon scope, focused unit + integration tests only
- Testing framework: `pytest==9.0.3`, `pytest-asyncio==1.4.0` — NO hypothesis
- All tasks are required (no optional markers)
- **⚠️ Cart version:** Initial version (0 vs 1) needs confirmation from Dev A before finalizing `CartService.create()`
- **⚠️ Cache import:** `from app.redis_client import get_redis` — exact function signature not frozen. Ask Dev A for final API before implementing `cache.py`
- Dev C does NOT create files in `app/models/` — all stubs live in `tests/stubs/`
- Seed script is intentionally last (Phase 8) because it depends on models, services, Redis, and DB being available

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["4.1"] },
    { "id": 4, "tasks": ["6.1"] },
    { "id": 5, "tasks": ["7.1", "7.2"] },
    { "id": 6, "tasks": ["9.1", "9.2", "9.3", "9.4"] },
    { "id": 7, "tasks": ["9.5", "9.6", "9.7", "9.8"] },
    { "id": 8, "tasks": ["9.9", "9.10", "9.11"] },
    { "id": 9, "tasks": ["11.1"] }
  ]
}
```
