# Intent-to-Cart: System Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Project:** Amazon Hackathon - Intent to Cart Backend

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Technology Stack](#technology-stack)
4. [Architecture Diagrams](#architecture-diagrams)
5. [Migration Management (Alembic)](#migration-management-alembic)
6. [API Endpoints](#api-endpoints)
7. [Core Workflows](#core-workflows)
8. [Security & Performance](#security--performance)
9. [Summary](#summary)

---

## Executive Summary

Intent-to-Cart is an AI-powered backend system designed to transform user natural language shopping intents into curated product bundles. The system intelligently interprets user input, clarifies ambiguous requirements through dialogue, and generates personalized three-tier product recommendations optimized for budget, classic, and premium experiences.

### Key Features:

- **Intent Classification**: NLP-based understanding of shopping intent
- **Interactive Clarification**: Multi-turn dialogue to refine user requirements
- **Intelligent Bundle Generation**: 12-step pipeline with personalization, inventory checks, ETA estimation
- **Smart Cart Management**: Redis-backed caching with versioning for optimistic locking
- **Checkout Orchestration**: Inventory verification, order placement, and preference learning

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend (React.js)                       │
│              (Sidebar, SmartAssistant, ProductGrid)             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Application Server                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Intent   │  │ Bundle   │  │ Cart     │  │ Checkout │        │
│  │ Router   │  │ Router   │  │ Router   │  │ Router   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│        │              │              │             │            │
│        └──────────────┴──────────────┴─────────────┘            │
│                       │                                         │
│        ┌──────────────┴──────────────┐                         │
│        ▼                             ▼                          │
│  ┌──────────────────┐       ┌──────────────────┐              │
│  │ Service Layer    │       │ Middleware Layer │              │
│  │                  │       │                  │              │
│  │ • BundleGenerator│       │ • RequestID      │              │
│  │ • CartService    │       │ • RequestTiming  │              │
│  │ • Checkout       │       │ • CORS           │              │
│  │ • Product        │       │ • Exception      │              │
│  │   Retrieval      │       │   Handlers       │              │
│  └──────────────────┘       └──────────────────┘              │
│        │                                                        │
│        ▼                                                        │
│  ┌────────────────────────────────────────────┐               │
│  │         Data Access & Cache Layer          │               │
│  │  ┌──────────────┐      ┌──────────────┐    │              │
│  │  │ Redis Cache  │      │ SQLAlchemy   │    │              │
│  │  │ • Bundles    │      │ ORM          │    │              │
│  │  │ • Carts      │      │ • Models     │    │              │
│  │  │ • Sessions   │      │ • Queries    │    │              │
│  │  └──────────────┘      └──────────────┘    │              │
│  └────────────────────────────────────────────┘               │
│        │                                                        │
│        ▼                                                        │
│  ┌────────────────────────────────────────────┐               │
│  │      External Integrations & Adapters      │               │
│  │  ┌──────────────┐  ┌──────────────┐        │              │
│  │  │ Inventory    │  │ Order        │        │              │
│  │  │ Adapter      │  │ Adapter      │        │              │
│  │  └──────────────┘  └──────────────┘        │              │
│  │  ┌──────────────┐  ┌──────────────┐        │              │
│  │  │ ETA Adapter  │  │ Product      │        │              │
│  │  │              │  │ Catalog      │        │              │
│  │  └──────────────┘  └──────────────┘        │              │
│  └────────────────────────────────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────────┘
        │                          │                    │
        ▼                          ▼                    ▼
   PostgreSQL           Redis Cache Server       External Services
   (Primary DB)         (Session/Cache)        (Inventory, Orders, ETA)
```

### Core Components:

| Component      | Purpose                                                      | Type           |
| -------------- | ------------------------------------------------------------ | -------------- |
| **Routers**    | Handle HTTP requests, validate inputs, route to services     | Presentation   |
| **Services**   | Business logic: bundle generation, cart operations, checkout | Business Logic |
| **Schemas**    | Pydantic data models for request/response validation         | Data Layer     |
| **Models**     | SQLAlchemy ORM models for database persistence               | Data Layer     |
| **Adapters**   | External service integrations (inventory, orders, ETA)       | Integration    |
| **Middleware** | Cross-cutting concerns (logging, timing, CORS, exceptions)   | Infrastructure |
| **Utilities**  | Cache, user utils, event emission                            | Infrastructure |

---

## Technology Stack

### Backend Framework & Libraries

| Category            | Technology     | Version  | Purpose                                          |
| ------------------- | -------------- | -------- | ------------------------------------------------ |
| **Framework**       | FastAPI        | 0.100+   | Async web framework with automatic documentation |
| **Async Runtime**   | Starlette      | Built-in | ASGI web server framework                        |
| **ORM**             | SQLAlchemy     | 2.0+     | Async-first SQL ORM with type hints              |
| **Database Driver** | asyncpg        | Latest   | High-performance async PostgreSQL driver         |
| **Cache**           | Redis          | Latest   | Distributed caching and session management       |
| **Redis Client**    | redis[asyncio] | Latest   | Async Redis client library                       |
| **Data Validation** | Pydantic       | v2.x     | Runtime type validation and serialization        |
| **Migrations**      | Alembic        | Latest   | Database schema versioning and migrations        |
| **Testing**         | pytest         | Latest   | Testing framework with async support             |
| **Mocking**         | unittest.mock  | Built-in | Mocking library for unit tests                   |

### Database Stack

| Component              | Technology              | Role                                 |
| ---------------------- | ----------------------- | ------------------------------------ |
| **Primary Database**   | PostgreSQL 12+          | OLTP database for persistent storage |
| **Async Connection**   | asyncpg                 | High-performance async driver        |
| **Migrations**         | Alembic + SQLAlchemy    | Schema versioning and management     |
| **Connection Pooling** | SQLAlchemy async engine | Manages async connection pool        |

### Caching & Session Management

| Component               | Technology        | Configuration                                  |
| ----------------------- | ----------------- | ---------------------------------------------- |
| **Cache Store**         | Redis             | In-memory data structure store                 |
| **Client**              | redis-py[asyncio] | Async Redis Python client                      |
| **TTL Strategy**        | Configurable      | Bundle: config-based, Cart: 24h, Buy-Again: 1h |
| **Cache-First Pattern** | Hybrid            | Read from Redis, fallback to DB                |

### Infrastructure

| Component            | Technology            | Purpose                      |
| -------------------- | --------------------- | ---------------------------- |
| **ASGI Server**      | Uvicorn               | Async Python web server      |
| **Containerization** | Docker                | Application containerization |
| **Orchestration**    | Kubernetes (Optional) | Container orchestration      |
| **Event System**     | Async fire-and-forget | Internal event emission      |
| **Logging**          | Python logging        | Structured logging           |

---

## Architecture Diagrams

### Data Flow: Intent Classification

```
┌──────────────────┐
│ User Input Text  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────┐
│ POST /v1/intent                  │
│ - Validate user authorization    │
│ - Extract user_id, session_id    │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ HybridParser.parse()             │
│ - LLM structured extraction      │
│ - Fallback: classify_hybrid()    │
│ Returns:                         │
│   - intent_type                  │
│   - entities[]                   │
│   - shopping_theme               │
│   - constraints{}                │
│   - confidence_score             │
│   - clarification_hints          │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Redis Cache Check                │
│ Key: intent:{intent_type}:bundle │
│ Cache Hit? → Return cached       │
│ Cache Miss? → Continue           │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Persist Intent_Model to DB       │
│ - Store all parsed data          │
│ - Record timestamp               │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Clarification Check              │
│ If confidence < 0.7 OR           │
│ missing_slots? → Initiate        │
│ ClarificationManager             │
│ Create session in Redis (900s)   │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ IntentResponse                   │
│ {                                │
│   intent_id,                     │
│   intent_type,                   │
│   confidence,                    │
│   entities[],                    │
│   clarification_question,        │
│   session_id (if needed)         │
│ }                                │
└──────────────────────────────────┘
```

### Data Flow: Bundle Generation Pipeline (12 Steps)

```
Step 1: Fetch Intent from DB ─────┐
                                   │
                                   ▼
Step 2: Verify User Ownership ◄───┘
                                   │
                                   ▼
Step 3: Redis Cache Check ────────┐
        (Key: bundle:{intent_type})│ Cache Hit → Return cached + metadata
                                   │ Cache Miss → Continue
                                   ▼
Step 4: PersonalizationService ──┐
        (Get user signals)         │
                                   ▼
Step 5: BundleGenerator ─────────┐
        (Generate 3 bundles)       │ Creates: budget, classic, premium
                                   │
                                   ▼
Step 6: InventoryAdapter ────────┐
        (Check stock for all)      │ Returns: available/warehouse
                                   │
                                   ▼
Step 7: ETAAdapter ──────────────┐
        (Estimate delivery)        │ Returns: eta_minutes, warehouse
                                   │
                                   ▼
Step 8: SubstitutionEngine ─────┐
        (Replace OOS items)        │ Suggested alternatives
                                   │
                                   ▼
Step 9: RankingEngine ──────────┐
        (Score bundles)            │ Weighted scoring: personalization,
                                   │ inventory, ETA, constraints
                                   ▼
Step 10: Persist to DB ─────────┐
         (Bundle_Model records)    │
                                   ▼
Step 11: Redis Cache ───────────┐
         (TTL: configurable)       │
                                   ▼
Step 12: Emit Event + Return ───┐
         bundle.generated event    │ Returns: recommended + all options
                                   ▼
         BundleListResponse
```

### Clarification Dialogue Flow

```
┌──────────────────────────┐
│ Clarification Initiated  │
│ (confidence < 0.7 OR     │
│  missing slots)          │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ ClarificationManager.resolve_question│
│ - Priority-ordered slot manager      │
│ - Determine missing information      │
│ - Generate first question            │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Store Session in Redis (900s TTL)    │
│ - answered_count                     │
│ - current_question                   │
│ - answered_questions[]               │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ Return ClarificationResponse         │
│ - Prompt user with question          │
└────────┬─────────────────────────────┘
         │ (User provides answer)
         ▼
┌──────────────────────────────────────┐
│ POST /v1/clarification               │
│ - Validate session exists            │
│ - Verify intent exists               │
│ - Persist answer to DB               │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ BundleContextBuilder.build()         │
│ - Merge intent constraints           │
│ - Merge clarification answers        │
│ - Extract quantity/budget/brand      │
│ - Build ConfirmedEntity list         │
│ - Resolve categories                 │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ answered_count < MAX (3)?            │
│ - YES: Get next question             │
│ - NO: complete=true, return context  │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ ClarificationResponse                │
│ - complete (bool)                    │
│ - next_question (str | null)         │
│ - bundle_context (if complete)       │
└──────────────────────────────────────┘
```

### Migration Management (Alembic)

**Location:** `backend/alembic/env.py`

**Configuration:**

- Async-first migrations using `asyncio.run()`
- SQLAlchemy 2.0+ async support
- Version tracking in `alembic_version` table

**Usage:**

```bash
# Create migration
alembic revision --autogenerate -m "Add user_preference"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## API Endpoints

### Summary Table

| Method | Endpoint                  | Purpose                | Auth     | Cache                    |
| ------ | ------------------------- | ---------------------- | -------- | ------------------------ |
| POST   | `/v1/intent`              | Classify intent        | Required | Hit check (results)      |
| GET    | `/v1/bundles/{intent_id}` | Generate bundles       | Required | Check + cache result     |
| POST   | `/v1/clarification`       | Clarification dialogue | Required | Session in Redis         |
| GET    | `/v1/cart/{cartId}`       | Retrieve cart          | Required | Redis-first              |
| POST   | `/v1/cart`                | Create cart            | Required | N/A                      |
| PATCH  | `/v1/cart/{cartId}`       | Modify cart            | Required | Redis + DB write-through |
| GET    | `/v1/buy-again`           | Previously ordered     | Required | 1h TTL                   |
| POST   | `/v1/checkout`            | Checkout & order       | Required | No-cache                 |
| GET    | `/health`                 | Health check           | Optional | N/A                      |
| GET    | `/metrics`                | Metrics                | Optional | N/A                      |

### Detailed Specifications

#### 1. Intent Classification

```
POST /v1/intent
Authorization: Bearer {token}
X-User-ID: {user_id}
Content-Type: application/json

{
  "text": "I need supplies for a dinner party this weekend",
  "session_id": "sess_12345"
}

Response (200):
{
  "intent_id": "uuid",
  "intent_type": "party_supplies",
  "confidence": 0.95,
  "entities": ["party supplies", "dinner"],
  "shopping_theme": "entertaining",
  "constraints": {
    "budget": 200,
    "quantity": null,
    "brand": null,
    "diet": null
  },
  "clarification_question": "How many guests are you expecting?",
  "session_id": "session_uuid"
}
```

---

#### 2. Bundle Generation

```
GET /v1/bundles/{intent_id}
Authorization: Bearer {token}
X-User-ID: {user_id}

Response (200):
{
  "intent_id": "uuid",
  "cache_hit": false,
  "recommended": {
    "bundle_id": "uuid",
    "bundle_type": "classic",
    "bundle_name": "Classic Option",
    "intent_type": "party_supplies",
    "items": [
      {
        "product_id": "PS-001",
        "name": "Party Plates (50 pack)",
        "brand": "Glad",
        "category": "disposables",
        "quantity": 2,
        "unit_price": 5.99,
        "image_url": "https://...",
        "is_substituted": false,
        "original_product_id": null,
        "eta_minutes": 480,
        "eta_label": "By tomorrow",
        "warehouse": "WH-Central"
      },
      // ... more items
    ],
    "total_price": 89.99,
    "final_score": 0.92
  },
  "options": [
    // ... budget and premium options
  ]
}
```

---

#### 3. Clarification Dialogue

```
POST /v1/clarification
Authorization: Bearer {token}
X-User-ID: {user_id}
Content-Type: application/json

{
  "intent_id": "uuid",
  "session_id": "session_uuid",
  "answer": "25 guests"
}

Response (200):
{
  "complete": false,
  "next_question": "What's your budget for party supplies?",
  "questions_remaining": 2,
  "answered_questions": [
    {
      "question": "How many guests are you expecting?",
      "answer": "25 guests"
    }
  ],
  "bundle_context": null  // null until complete=true
}

Final Response (when complete=true):
{
  "complete": true,
  "next_question": null,
  "questions_remaining": 0,
  "answered_questions": [...],
  "bundle_context": {
    "intent_id": "uuid",
    "intent_type": "party_supplies",
    "shopping_theme": "entertaining",
    "resolved_category": "party_supplies",
    "confirmed_entities": [
      {
        "raw": "party supplies",
        "canonical": "party supplies",
        "brand": null,
        "quantity": 25,
        "unit": "items"
      }
    ],
    "constraints": {
      "quantity": 25,
      "budget": 300,
      "brand": null,
      "diet": null
    },
    "semantic_query": "party supplies for 25 people",
    "category_query": "party_supplies",
    "product_query_hints": ["disposables", "beverages", "snacks"]
  }
}
```

---

#### 4. Cart Operations

```
POST /v1/cart
Authorization: Bearer {token}
X-User-ID: {user_id}
Content-Type: application/json

{
  "bundleId": "uuid"  // optional
}

Response (200):
{
  "cartId": "uuid",
  "version": 1,
  "items": [],
  "total": 0.0,
  "status": "active"
}

---

PATCH /v1/cart/{cartId}
Authorization: Bearer {token}
X-User-ID: {user_id}
Content-Type: application/json

{
  "operations": [
    {
      "type": "add",
      "productId": "PS-001",
      "quantity": 2
    },
    {
      "type": "update",
      "productId": "PS-002",
      "quantity": 1
    }
  ],
  "version": 1  // optional, for optimistic locking
}

Response (200):
{
  "cartId": "uuid",
  "version": 2,
  "items": [
    {
      "productId": "PS-001",
      "productName": "Party Plates",
      "quantity": 2,
      "price": 5.99,
      "imageUrl": "https://...",
      "brand": "Glad",
      "category": "disposables",
      "unit": "pack",
      "isSubstituted": false
    }
  ],
  "total": 89.99,
  "status": "active"
}
```

---

#### 5. Checkout

```
POST /v1/checkout
Authorization: Bearer {token}
X-User-ID: {user_id}
Content-Type: application/json

{
  "cartId": "uuid"
}

Response (200):
{
  "orderId": "order-12345",
  "status": "confirmed",
  "summary": {
    "itemCount": 5,
    "total": 89.99,
    "estimatedDelivery": "2026-06-16"
  }
}

Error (409) - Out of Stock:
{
  "error": {
    "code": "ITEMS_OUT_OF_STOCK",
    "message": "Some items are out of stock"
  },
  "outOfStockItems": [
    {
      "productId": "PS-001",
      "availableQuantity": 0,
      "substitutes": [
        {
          "productId": "PS-002",
          "name": "Party Plates (75 pack)",
          "price": 6.99
        }
      ]
    }
  ]
}
```

## Core Workflows

### Complete User Journey

````
1. USER INTENT PHASE
   ├─ User: "I need supplies for a dinner party"
   ├─ POST /v1/intent
   ├─ Server: Parse + classify
   ├─ Server: Check confidence
   ├─ Low confidence? → Initiate clarification
   └─ Response: intent_id + session_id

2. CLARIFICATION PHASE (if needed)
   ├─ Server: Get first question
   ├─ Response: "How many guests?"
   ├─ User: "25 guests"
   ├─ POST /v1/clarification
   ├─ Server: Store answer
   ├─ More questions? → Return next question
   ├─ All answered? → Build BundleContext
   └─ Response: complete=true, context

3. BUNDLE GENERATION PHASE
   ├─ User: View recommended bundle
   ├─ GET /v1/bundles/{intent_id}
   ├─ Server: 12-step pipeline
   │  ├─ Load intent from DB
   │  ├─ Check Redis cache
   │  ├─ Personalize based on user signals
   │  ├─ Generate 3 bundles
   │  ├─ Check inventory
   │  ├─ Get ETA
   │  ├─ Apply substitutions
   │  ├─ Rank bundles
   │  ├─ Persist to DB
   │  └─ Cache result
   ├─ Emit: bundle.generated
   └─ Response: recommended + all options

4. CART PHASE
   ├─ User: Select items from bundle
   ├─ POST /v1/cart
   ├─ Server: Create new cart
   ├─ Response: cartId
   │
   ├─ User: Add items
   ├─ PATCH /v1/cart/{cartId}
   ├─ Server: Apply operations
   ├─ Server: Cache in Redis + DB
   ├─ Emit: cart.updated
   └─ Response: updated cart
   │
   ├─ [Repeat for modify/remove operations]
   │
   └─ User: Review cart

---

### Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@neon-db.postgresql.net/intent_to_cart

# Redis
REDIS_URL=redis://redis-cluster:6379/0

# Application
DEBUG=False
MAX_WORKERS=4

# API
API_VERSION=1.0.0
CORS_ORIGINS=["https://frontend.example.com", ...]

# Clarification
MAX_CLARIFICATION_QUESTIONS=3
CLARIFICATION_SESSION_TTL=900

# Bundle Generation
BUNDLE_CACHE_TTL=3600
PERSONALIZATION_MODEL_PATH=/models/personalization.pkl

# External Services
INVENTORY_API_URL=https://inventory-api.internal
ORDER_API_URL=https://order-api.internal
ETA_API_URL=https://eta-api.internal
````

---

## Security & Performance

### Security Measures

1. **Authentication:**
   - OAuth2 with JWT tokens
   - X-User-ID header extraction
   - Token validation on every request

2. **Authorization:**
   - User ownership verification (intent, cart, order)
   - Cannot access other users' data

3. **Input Validation:**
   - Pydantic automatic validation
   - Field constraints (min/max length, numeric ranges)
   - Type checking

4. **Error Handling:**
   - No internals exposed in error messages
   - Structured error responses
   - Logging for debugging

5. **Data Protection:**
   - PostgreSQL at rest encryption (optional)
   - Redis authentication
   - TLS for external service calls

### Performance Optimizations

1. **Caching Strategy:**
   - Redis-first for bundles, carts, buy-again
   - Write-through for consistency
   - Fire-and-forget error handling

2. **Database Optimization:**
   - Connection pooling (20 connections, 10 overflow)
   - Prepared statements (SQLAlchemy ORM)
   - Async operations (no blocking)
   - Warm pool on startup

3. **Batch Operations:**
   - Inventory checks in batch
   - ETA retrieval in parallel
   - Substitution lookup optimized

4. **Async Processing:**
   - Non-blocking user preference updates
   - Background event publishing
   - No synchronous external calls in critical path

5. **Query Optimization:**
   - Indexed fields: user_id, intent_id, status
   - Efficient joins for buy-again
   - Pagination for large result sets

### Monitoring & Observability

1. **Metrics:**
   - Cache hit/miss rates
   - Request latency (via X-Process-Time header)
   - Intent confidence distribution
   - Clarification question statistics

2. **Logging:**
   - Request ID propagation (X-Request-ID)
   - Structured logging with context
   - Error stack traces
   - Database query logging (debug mode)

3. **Health Checks:**
   - `/health` endpoint
   - Database connectivity
   - Redis connectivity
   - External service availability

---

## Summary

The Intent-to-Cart backend is a sophisticated, production-ready system designed to transform user shopping intents into intelligent, personalized product bundles.

**Key Architectural Strengths:**

✅ **Asynchronous Design** - Non-blocking I/O for maximum concurrency  
✅ **Intelligent Caching** - Redis-backed with fire-and-forget error handling  
✅ **Modular Services** - Clear separation of concerns, testable components  
✅ **Type-Safe** - Pydantic validation at every boundary  
✅ **Observable** - Request tracking, metrics, structured logging  
✅ **Scalable** - Stateless servers, database connection pooling  
✅ **Extensible** - Adapter pattern for external integrations

**Technology Excellence:**

- **FastAPI**: Modern, fast Python framework with automatic documentation
- **SQLAlchemy 2.0+**: Async-first ORM with type hints
- **PostgreSQL**: Reliable ACID-compliant relational database
- **Redis**: High-performance distributed cache
- **Pydantic v2**: Runtime data validation and serialization

This architecture supports millions of requests, complex business logic, and seamless integration with external services while maintaining code quality and operational simplicity.

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Status:** Complete & Production-Ready
