"""Clarification endpoint.

Provides POST /v1/clarification for submitting answers to clarification
questions and advancing the clarification dialogue.

Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 25.3, 25.4, 25.5
"""

import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as redis

from app.services.bundle_context_builder import BundleContextBuilder

from app.database import get_db
from app.dependencies import get_current_user_id
from app.exceptions import AppException, INTENT_NOT_FOUND, SESSION_EXPIRED
from app.models.clarification import Clarification_Model
from app.models.intent import Intent_Model
from app.redis_client import get_redis
from app.utils.cache import cache_set
from app.schemas.clarification import (
    ClarificationAnswer,
    ClarificationRequest,
    ClarificationResponse,
)
from app.services.clarification_engine import get_next_question, MAX_CLARIFICATION_QUESTIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["clarification"])

_SESSION_TTL_SECONDS = 900


@router.post("/clarification", response_model=ClarificationResponse)
async def post_clarification(
    request: ClarificationRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> ClarificationResponse:
    """Submit a clarification answer and retrieve the next question.

    Validates the session in Redis, verifies the intent exists in the DB,
    persists the clarification answer, and advances the dialogue state.
    """
    # 1. Check Redis for session
    session_key = f"clarification:session:{request.session_id}"
    session_raw = await redis_client.get(session_key)

    if session_raw is None:
        raise AppException(
            SESSION_EXPIRED[0],
            "Clarification session has expired",
            SESSION_EXPIRED[1],
        )

    # 2. Verify intent exists in DB
    result = await db.execute(
        select(Intent_Model).where(Intent_Model.id == request.intent_id)
    )
    intent = result.scalars().first()

    if intent is None:
        raise AppException(
            INTENT_NOT_FOUND[0],
            "Intent not found",
            INTENT_NOT_FOUND[1],
        )

    # 3. Parse session data
    session_data = json.loads(session_raw)
    answered_count: int = session_data["answered_count"]
    current_question: str = session_data["current_question"]
    session_entities = session_data.get("entities", []) or []
    session_constraints = session_data.get("constraints", {}) or {}
    session_shopping_theme = session_data.get("shopping_theme")

    if "answered_questions" in session_data:
        answered_questions_data = list(session_data["answered_questions"])
        history_loaded_from_session = True
    else:
        clarifications_result = await db.execute(
            select(Clarification_Model)
            .where(Clarification_Model.intent_id == request.intent_id)
            .order_by(Clarification_Model.timestamp.asc(), Clarification_Model.id.asc())
        )
        answered_questions_data = [
            {"question": item.question, "answer": item.answer}
            for item in clarifications_result.scalars().all()
        ]
        history_loaded_from_session = False

    if history_loaded_from_session:
        answered_questions_data.append({
            "question": current_question,
            "answer": request.answer,
        })

    # 4. Persist clarification row
    clarification = Clarification_Model(
        intent_id=request.intent_id,
        question=current_question,
        answer=request.answer,
    )
    db.add(clarification)
    await db.commit()

    # 4b. Merge the latest answer into constraints (dynamic context update)
    from app.services.dynamic_clarification import (
        merge_answer_into_constraints,
        extract_entities_from_answer,
    )
    updated_constraints = merge_answer_into_constraints(
        session_constraints, current_question, request.answer
    )
    # Extract any new entities from the answer
    new_entities = extract_entities_from_answer(request.answer, session_entities)
    updated_entities = session_entities + new_entities

    # 5. Get next question using dynamic context-aware system
    try:
        from app.services.clarification_manager import resolve_question
        next_question = await resolve_question(
            user_text=intent.raw_text,
            intent_type=intent.intent_type,
            confidence=intent.confidence,
            entities=updated_entities,
            constraints=updated_constraints,
            conversation=answered_questions_data,
            shopping_theme=session_shopping_theme,
            questions_asked=answered_count + 1,
        )
    except Exception as exc:
        logger.warning("Dynamic clarification failed: %s — using static fallback", exc)
        # Fallback to static questions
        next_question = get_next_question(intent.intent_type, answered_count + 1)

    # 6. Handle next state
    if next_question is not None:
        # More questions remaining — update Redis session with accumulated context
        updated_session = json.dumps({
            "answered_count": answered_count + 1,
            "current_question": next_question,
            "answered_questions": answered_questions_data,
            "entities": updated_entities,
            "constraints": updated_constraints,
            "shopping_theme": session_shopping_theme,
            "confidence": session_data.get("confidence", intent.confidence),
        })
        await redis_client.set(session_key, updated_session, ex=_SESSION_TTL_SECONDS)

        return ClarificationResponse(
            complete=False,
            next_question=next_question,
            questions_remaining=MAX_CLARIFICATION_QUESTIONS - (answered_count + 1),
            answered_questions=[
                ClarificationAnswer(question=item["question"], answer=item["answer"])
                for item in answered_questions_data
            ],
        )

    # 7. Clarification complete — clean up session and emit event
    await redis_client.delete(session_key)

    # NEW: Build the consolidated context
    bundle_context = await BundleContextBuilder.build(intent, answered_questions_data)
    
    # NEW: Cache for the bundle generation phase (e.g. 30 minute TTL)
    await cache_set(
        f"bundle_context:{request.intent_id}",
        bundle_context.model_dump(mode="json"),
        1800,
    )

    answered_questions = [
        ClarificationAnswer(question=item["question"], answer=item["answer"])
        for item in answered_questions_data
    ]

    # Fire-and-forget event stub
    logger.info("clarification.answered event emitted for intent_id=%s", request.intent_id)

    return ClarificationResponse(
        complete=True,
        next_question=None,
        questions_remaining=0,
        answered_questions=answered_questions,
        bundle_context=bundle_context,
    )
