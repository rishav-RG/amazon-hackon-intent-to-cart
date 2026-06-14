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

from app.database import get_db
from app.dependencies import get_current_user_id
from app.exceptions import AppException, INTENT_NOT_FOUND, SESSION_EXPIRED
from app.models.clarification import Clarification_Model
from app.models.intent import Intent_Model
from app.redis_client import get_redis
from app.schemas.clarification import ClarificationRequest, ClarificationResponse
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

    # 4. Persist clarification row
    clarification = Clarification_Model(
        intent_id=request.intent_id,
        question=current_question,
        answer=request.answer,
    )
    db.add(clarification)
    await db.commit()

    # 5. Get next question (try LLM-powered smart question, fallback to static)
    try:
        from app.services.clarification_engine import get_next_question_smart
        # Collect previous questions from session
        previous_questions = [current_question]
        next_question = await get_next_question_smart(
            user_text=intent.raw_text,
            intent_type=intent.intent_type,
            confidence=intent.confidence,
            entities=[],  # entities not stored in session currently
            previous_questions=previous_questions,
            answered_count=answered_count + 1,
        )
    except Exception:
        # Fallback to static questions
        next_question = get_next_question(intent.intent_type, answered_count + 1)

    # 6. Handle next state
    if next_question is not None:
        # More questions remaining — update Redis session
        updated_session = json.dumps({
            "answered_count": answered_count + 1,
            "current_question": next_question,
        })
        await redis_client.set(session_key, updated_session, ex=_SESSION_TTL_SECONDS)

        return ClarificationResponse(
            complete=False,
            next_question=next_question,
            questions_remaining=MAX_CLARIFICATION_QUESTIONS - (answered_count + 1),
        )

    # 7. Clarification complete — clean up session and emit event
    await redis_client.delete(session_key)

    # Fire-and-forget event stub (Event_Bus owned by Dev C)
    logger.info(
        "clarification.answered event emitted for intent_id=%s, session_id=%s",
        request.intent_id,
        request.session_id,
    )

    return ClarificationResponse(
        complete=True,
        next_question=None,
        questions_remaining=0,
    )
