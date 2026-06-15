# Requirements Document

## Introduction

Dev C's infrastructure layer for the Intent-to-Cart Engine backend. This covers the event bus, cache utilities, cart service, checkout service, cart/checkout/buy-again routers, Pydantic schemas, and a seed script. The code must be independently runnable using stub/mock implementations of Dev A's data-layer interfaces and Dev B's external-service adapters.

All stubs live exclusively in `tests/stubs/` — Dev C does NOT create files in `app/models/` (owned by Dev A).

### Implementation Phase Order

For context on dependency ordering:

- **Phase 1:** `app/events.py`, `app/utils/cache.py`
- **Phase 2:** `app/schemas/cart.py`, `app/schemas/checkout.py`
- **Phase 3:** `app/services/cart_service.py` (depends on Dev A models)
- **Phase 4:** `app/routers/cart.py`
- **Phase 5:** `app/services/checkout_service.py` (depends on Dev B adapters)
- **Phase 6:** `app/routers/checkout.py`, `app/routers/buy_again.py`

## Glossary

- **Cart_Service**: The service layer responsible for cart CRUD operations with optimistic locking, Redis-primary storage, and DB write-through. Exposes `create()` for new carts and mutation methods for add/remove/update operations.
- **Checkout_Service**: The service layer that fetches the cart from Postgres (hard read), validates cart state, performs hard inventory checks, places orders via OrderAdapter, updates cart status, triggers async UserPreference update, and emits events.
- **Event_Bus**: An in-process asyncio publish/subscribe mechanism that emits named events with JSON payloads and logs to stdout.
- **Cache_Utils**: Helper module (`app/utils/cache.py`) wrapping Redis get/set/delete operations with JSON serialization and configurable TTL.
- **Cart_Router**: FastAPI router exposing `PATCH /v1/cart` (cart mutations) and `GET /v1/cart/{cartId}` (get cart state).
- **Checkout_Router**: FastAPI router exposing `POST /v1/checkout` (checkout a cart).
- **Buy_Again_Router**: FastAPI router exposing `GET /v1/buy-again` (buy-again rail for the current user, identified via `X-User-ID` header).
- **Stub_Layer**: Mock implementations located exclusively in `tests/stubs/` for Dev A's interfaces (redis_client, Cart/CartItem/UserPreference models, AsyncSession) and Dev B's interfaces (InventoryAdapter, OrderAdapter, ProductCatalogAdapter) enabling independent execution and testing.
- **Seed_Script**: `backend/seed.py` — an idempotent script that populates the database and Redis with sample data for local development.
- **Optimistic_Lock**: A concurrency control mechanism where the client sends a `version` field in the PATCH body. The server rejects updates if the version does not match the stored version.
- **OOS**: Out-of-stock — an inventory state where requested quantity is unavailable.
- **Cart_Operation**: A single mutation instruction within a PATCH body. Type is one of: `add`, `remove`, `update`.

## Requirements

### Requirement 1: Event Bus

**User Story:** As a backend developer, I want an in-process event bus so that services can communicate state changes asynchronously without tight coupling.

#### Acceptance Criteria

1. THE Event_Bus SHALL expose an async `emit(event_name: str, payload: dict)` method that publishes the event to all registered subscribers.
2. WHEN `emit` is called, THE Event_Bus SHALL log the event_name and payload to stdout in JSON format.
3. THE Event_Bus SHALL expose a `subscribe(event_name: str, handler: Callable)` method that registers an async handler for the given event name.
4. WHEN an event is emitted, THE Event_Bus SHALL invoke all handlers subscribed to that event_name concurrently using asyncio.
5. IF a subscriber handler raises an exception, THEN THE Event_Bus SHALL log the exception to stdout and continue invoking remaining handlers.

---

### Requirement 2: Cache Utilities

**User Story:** As a backend developer, I want a cache utility module so that services read and write JSON-serialized data to Redis with consistent TTL handling.

#### Acceptance Criteria

1. THE Cache_Utils SHALL expose an async `cache_get(key: str) -> Optional[dict]` method that retrieves and JSON-deserializes the value from Redis.
2. THE Cache_Utils SHALL expose an async `cache_set(key: str, value: dict, ttl: int) -> None` method that JSON-serializes the value and stores it in Redis with the specified TTL in seconds.
3. THE Cache_Utils SHALL expose an async `cache_delete(key: str) -> None` method that removes the key from Redis.
4. IF Redis is unreachable during a cache operation, THEN THE Cache_Utils SHALL handle the Redis connection error gracefully and re-raise with context information attached.

> **Note:** The exact error type (`CacheUnavailableError` vs `AppException`) requires confirmation from Dev A. Reference `app/utils/exceptions.py` as the source of truth for error types.

---

### Requirement 3: Cart Service

**User Story:** As a user, I want to manage items in my cart so that I can accumulate products before checkout.

#### Acceptance Criteria

1. WHEN a PATCH request contains operations and no cartId exists for the user, THE Cart_Service SHALL call `Cart_Service.create()` to initialize a new cart before applying operations.
2. WHEN a PATCH request contains an `add` operation, THE Cart_Service SHALL add the item to the cart, increment the cart version, persist the cart to Redis with key `cart:{cartId}` and TTL 86400 seconds, and write-through to the database.
3. WHEN a PATCH request contains a `remove` operation, THE Cart_Service SHALL remove the item from the cart, increment the cart version, persist the cart to Redis with key `cart:{cartId}` and TTL 86400 seconds, and write-through to the database.
4. WHEN a PATCH request contains an `update` operation, THE Cart_Service SHALL update the item quantity, increment the cart version, persist the cart to Redis with key `cart:{cartId}` and TTL 86400 seconds, and write-through to the database.
5. WHEN a cart mutation succeeds, THE Cart_Service SHALL emit a `cart.updated` event via the Event_Bus with payload containing cartId, userId, version, and itemCount.
6. WHEN a PATCH request includes a `version` field that does not match the current server version, THE Cart_Service SHALL reject the request with HTTP 409 and a response body containing the current server version and the full current cart state.
7. WHEN a get-cart request is received, THE Cart_Service SHALL read from Redis first; IF the Redis key is missing, THEN THE Cart_Service SHALL fall back to the database query.

---

### Requirement 4: Cart Router

**User Story:** As a frontend developer, I want cart endpoints so that the UI can manage the user's cart.

#### Acceptance Criteria

1. THE Cart_Router SHALL expose a `PATCH /v1/cart` endpoint that accepts a JSON body containing `{ operations: [...], version?: int }` where each operation specifies a type (`add`, `remove`, or `update`) and relevant fields.
2. WHEN the PATCH request succeeds, THE Cart_Router SHALL return HTTP 200 with a response body containing `{ cartId, version, items, total }`.
3. WHEN a PATCH request results in a version conflict, THE Cart_Router SHALL return HTTP 409 with the current server version and full cart state in the response body.
4. THE Cart_Router SHALL expose a `GET /v1/cart/{cartId}` endpoint that returns the current cart state including cartId, version, items, total, and status.
5. WHEN a PATCH request is received and no cartId exists for the user, THE Cart_Router SHALL delegate to Cart_Service.create() to initialize a new cart before applying operations.

---

### Requirement 5: Checkout Service

**User Story:** As a user, I want to check out my cart so that my selected items are converted into an order.

#### Acceptance Criteria

1. WHEN a checkout request is received, THE Checkout_Service SHALL fetch the cart from Postgres using a hard database read (NOT from cache).
2. WHEN the cart is fetched, THE Checkout_Service SHALL validate that the cart status is active and that the cart contains at least one item.
3. IF the cart status is not active, THEN THE Checkout_Service SHALL return HTTP 400 with a message indicating the cart is not in an active state.
4. IF the cart contains zero items, THEN THE Checkout_Service SHALL return HTTP 400 with a message indicating the cart is empty.
5. WHEN validation passes, THE Checkout_Service SHALL call InventoryAdapter.check_batch() to perform a hard inventory check against all cart items (no cache bypass).
6. IF one or more items are out-of-stock and no substitution is available, THEN THE Checkout_Service SHALL return HTTP 422 with error code `ITEMS_OUT_OF_STOCK` and a response body listing the OOS items.
7. WHEN all items pass the inventory check, THE Checkout_Service SHALL call OrderAdapter.place_order() to create the order.
8. WHEN order placement succeeds, THE Checkout_Service SHALL update the cart status to indicate it is no longer active.
9. WHEN order placement succeeds, THE Checkout_Service SHALL trigger an async UserPreference update for the user.
10. WHEN order placement succeeds, THE Checkout_Service SHALL emit an `order.placed` event via the Event_Bus with payload containing orderId, cartId, userId, and itemCount.

---

### Requirement 6: Checkout Router

**User Story:** As a frontend developer, I want a checkout endpoint so that the UI can submit a cart for order placement.

#### Acceptance Criteria

1. THE Checkout_Router SHALL expose a `POST /v1/checkout` endpoint that accepts a JSON body containing `{ cartId }`.
2. WHEN checkout succeeds, THE Checkout_Router SHALL return HTTP 200 with a response body containing `{ orderId, status: "confirmed", items, total }`.
3. IF checkout fails due to OOS items, THEN THE Checkout_Router SHALL return HTTP 422 with error code `ITEMS_OUT_OF_STOCK` and the list of OOS items.
4. IF checkout fails due to invalid cart state, THEN THE Checkout_Router SHALL return HTTP 400 with a descriptive error message.

---

### Requirement 7: Buy-Again Router

**User Story:** As a user, I want to see my previously ordered items so that I can quickly re-add them to a new cart.

#### Acceptance Criteria

1. THE Buy_Again_Router SHALL expose a `GET /v1/buy-again` endpoint that returns a list of previously ordered items for the current user.
2. THE Buy_Again_Router SHALL identify the current user via the `X-User-ID` header using the `get_current_user_id` dependency.
3. WHEN the request is received, THE Buy_Again_Router SHALL read from Redis cache key `buy_again:{userId}` with TTL 3600 seconds.
4. IF the Redis cache key is missing, THEN THE Buy_Again_Router SHALL fall back to querying Cart joined with CartItem from the database and enriching results via ProductCatalogAdapter.
5. WHEN a database fallback query succeeds, THE Buy_Again_Router SHALL populate the Redis cache key `buy_again:{userId}` with the result and TTL 3600 seconds before returning the response.

---

### Requirement 8: Pydantic Schemas

**User Story:** As a backend developer, I want well-defined request/response schemas so that API contracts are validated automatically.

#### Acceptance Criteria

1. THE Schemas module SHALL define Pydantic v2 models for cart operation schemas: `AddOperation` (productId, quantity), `RemoveOperation` (productId), `UpdateOperation` (productId, quantity) each with a `type` discriminator field.
2. THE Schemas module SHALL define a `CartPatchRequest` model containing `operations: list[CartOperation]` and `version: Optional[int]`.
3. THE Schemas module SHALL define a `CartResponse` model containing fields: cartId, version, items, total, status.
4. THE Schemas module SHALL define a `CheckoutRequest` model containing field: cartId.
5. THE Schemas module SHALL define a `CheckoutResponse` model containing fields: orderId, status, items, total.
6. THE Schemas module SHALL define an `OOSErrorDetail` model containing fields: productId, availableQuantity, and substitutes.
7. THE Schemas module SHALL define a `BuyAgainItem` model containing fields: productId, productName, lastOrderedAt.
8. THE Schemas module SHALL use Pydantic v2 field validators to enforce that quantity values are positive integers.
9. THE Schemas module SHALL use Pydantic v2 field validators to enforce that version values are non-negative integers.

---

### Requirement 9: Stub/Mock Layer

**User Story:** As Dev C, I want stub implementations of Dev A's and Dev B's interfaces so that my code is runnable and testable without their completed modules.

#### Acceptance Criteria

1. THE Stub_Layer SHALL reside exclusively in the `tests/stubs/` directory.
2. THE Stub_Layer SHALL NOT create any files in `app/models/` (owned by Dev A).
3. THE Stub_Layer SHALL provide a mock `redis_client` module exposing async get, set, and delete methods that operate on an in-memory dictionary.
4. THE Stub_Layer SHALL provide stub SQLAlchemy models for Cart, CartItem, and UserPreference matching the expected column schema.
5. THE Stub_Layer SHALL provide a mock `database` module exposing an async session factory that returns a functional AsyncSession connected to an in-memory SQLite database or mock object.
6. THE Stub_Layer SHALL provide a stub InventoryAdapter with an async `check_batch(items: list) -> dict` method that returns configurable stock/substitute data.
7. THE Stub_Layer SHALL provide a stub OrderAdapter with an async `place_order(cart) -> str` method that returns a generated order_id string.
8. THE Stub_Layer SHALL provide a stub ProductCatalogAdapter with an async method that returns product metadata for given product IDs.

---

### Requirement 10: Seed Script

**User Story:** As a developer, I want a seed script so that I can quickly populate the local environment with sample data for manual testing.

#### Acceptance Criteria

1. THE Seed_Script SHALL be located at `backend/seed.py`.
2. THE Seed_Script SHALL be idempotent — running it multiple times produces the same final state without duplicating data.
3. WHEN executed, THE Seed_Script SHALL insert sample Cart and CartItem records into the database.
4. WHEN executed, THE Seed_Script SHALL populate corresponding Redis cache keys (`cart:{cartId}`) with the seeded cart data and TTL 86400 seconds.
5. WHEN executed, THE Seed_Script SHALL populate at least one `buy_again:{userId}` Redis cache key with sample data and TTL 3600 seconds.
6. THE Seed_Script SHALL be executable via `python seed.py` from the backend directory.
