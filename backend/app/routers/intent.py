"""
Intent classification router.

Provides POST /v1/intent endpoint for classifying user intent text,
caching bundles, persisting results, and triggering clarification flows.

Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8,
           25.1, 25.2, 26.1, 26.2, 26.3, 26.4, 26.5, 26.6
"""

import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.database import get_db
from app.dependencies import get_current_user_id
from app.metrics import metrics
from app.models.intent import Intent_Model
from app.redis_client import get_redis
from app.schemas.intent import IntentRequest, IntentResponse, ShoppingConstraints
from app.services import clarification_engine, clarification_manager, hybrid_parser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["intent"])


@router.post("/intent", response_model=IntentResponse)
async def classify_intent(
    request: IntentRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> IntentResponse:
    """Classify user intent text and return structured result.

    Steps:
    1. Classify text via Intent_Engine
    2. Check Redis cache for pre-built bundle
    3. Persist Intent_Model to database
    4. If low confidence, initiate clarification flow
    5. Emit intent.created event (stub)
    6. Increment metrics counters
    7. Return IntentResponse
    """
    # Step 1: Hybrid parse (LLM structured parser → fallback classify_hybrid)
    # Returns intent_type (mapped to existing enum), entities, shopping_theme,
    # constraints, and clarification hints. NEVER raises.
    result = await hybrid_parser.parse(request.text)

    # Step 2: Check Redis cache for bundle
    cached_bundle = None
    try:
        cache_key = f"intent:{result.intent_type}:bundle"
        cached_data = await redis_client.get(cache_key)
        if cached_data is not None:
            cached_bundle = json.loads(cached_data)
            metrics.record_cache_hit()
        else:
            metrics.record_cache_check()
    except Exception as exc:
        # Cache errors are fire-and-forget — don't fail the request
        logger.warning("Cache lookup failed for key '%s': %s", cache_key, exc)

    # Step 3: Persist intent to database (now includes hybrid slots)
    intent = Intent_Model(
        user_id=user_id,
        session_id=request.session_id,
        raw_text=request.text,
        intent_type=result.intent_type,
        confidence=result.confidence,
        shopping_theme=result.shopping_theme,
        entities=result.entities,
        constraints=result.constraints,
    )
    db.add(intent)
    await db.commit()
    await db.refresh(intent)

    # Step 4: Clarification via dynamic context-aware system.
    # Triggers when slots are missing OR confidence < 0.7 (preserves old behavior).
    clarification_question = None
    needs_clar = result.needs_clarification or result.confidence < 0.7
    if needs_clar:
        try:
            clarification_question = await clarification_manager.resolve_question(
                user_text=request.text,
                intent_type=result.intent_type,
                confidence=result.confidence,
                entities=result.entities,
                constraints=result.constraints,
                llm_suggested=result.clarification_question,
                conversation=[],  # No conversation yet — this is the initial question
                shopping_theme=result.shopping_theme,
                questions_asked=0,
            )
            # Final safety net: static first question
            if clarification_question is None and result.confidence < 0.7:
                clarification_question = clarification_engine.get_first_question(
                    result.intent_type
                )
        except Exception:
            clarification_question = clarification_engine.get_first_question(
                result.intent_type
            )

        # Store clarification session in Redis with TTL 900s (unchanged)
        if clarification_question is not None:
            session_data = json.dumps({
                "intent_id": str(intent.id),
                "intent_type": result.intent_type,
                "answered_count": 0,
                "current_question": clarification_question,
                "answered_questions": [],
                "shopping_theme": result.shopping_theme,
                "entities": result.entities,
                "constraints": result.constraints,
                "confidence": result.confidence,
            })
            try:
                session_key = f"clarification:session:{request.session_id}"
                await redis_client.set(session_key, session_data, ex=900)
            except Exception as exc:
                logger.warning(
                    "Failed to store clarification session '%s': %s",
                    request.session_id,
                    exc,
                )

    # Step 5: Emit intent.created event (Dev C stub — fire-and-forget log)
    logger.info(
        "Event intent.created: intent_id=%s user_id=%s intent_type=%s confidence=%.3f",
        intent.id,
        user_id,
        result.intent_type,
        result.confidence,
    )

    # Step 6: Increment metrics counters
    metrics.increment_intent()
    if result.intent_type == "checkout":
        metrics.increment_checkout()

    # Step 7: Return response (now includes hybrid slots)
    return IntentResponse(
        intent_id=intent.id,
        intent_type=result.intent_type,
        confidence=result.confidence,
        entities=result.entities,
        clarification_question=clarification_question,
        cached_bundle=cached_bundle,
        llm_used=result.llm_used,
        fallback=result.fallback,
        shopping_theme=result.shopping_theme,
        constraints=ShoppingConstraints(**result.constraints) if result.constraints else None,
        resolved_category=None,  # resolved later at bundle time
        needs_clarification=clarification_question is not None,
    )
