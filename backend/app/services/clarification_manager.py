"""
Clarification Manager — Dynamic context-aware question generation.

Decides whether clarification is needed for a parsed shopping intent and
produces the next question using:
1. Stopping criteria (is there enough context already?)
2. Mandatory slot reservation (quantity + budget in final 2 slots)
3. LLM-driven dynamic question generation (full conversation context)
4. Static fallback when LLM is unavailable

This module composes:
- dynamic_clarification.py (new context-aware system)
- clarification_engine.py (legacy static fallback)

API is backward-compatible: resolve_question() and needs_clarification()
have the same signatures as before.
"""

import logging
from typing import Optional

from app.services.dynamic_clarification import (
    ClarificationContext,
    generate_next_question,
    should_stop,
    merge_answer_into_constraints,
    MAX_QUESTIONS,
)

logger = logging.getLogger(__name__)

# Legacy static slot questions (used as absolute last fallback)
SLOT_QUESTIONS = {
    "entity": "What specific products are you looking for?",
    "quantity": "How many would you like?",
    "budget": "Do you have a budget in mind?",
    "brand": "Any preferred brand?",
    "diet": "Any dietary preferences or restrictions?",
}

SLOT_PRIORITY = ["entity", "quantity", "budget", "brand", "diet"]


def _slot_missing(slot: str, entities: list[str], constraints: dict) -> bool:
    """Return True if the given slot is unfilled."""
    if slot == "entity":
        return not entities
    value = (constraints or {}).get(slot)
    return value is None


def next_question(
    entities: list[str],
    constraints: dict,
    llm_suggested: Optional[str] = None,
) -> Optional[str]:
    """
    Return the next clarification question by slot priority, or None if all
    priority slots are sufficiently filled.

    This is the LEGACY synchronous API — kept for backward compatibility.
    For the full dynamic system, use resolve_question_dynamic().
    """
    constraints = constraints or {}

    # Mandatory: entity must be present
    if _slot_missing("entity", entities, constraints):
        return llm_suggested or SLOT_QUESTIONS["entity"]

    # Soft slots: ask for at most the single highest-priority missing one.
    for slot in SLOT_PRIORITY[1:]:
        if _slot_missing(slot, entities, constraints):
            return llm_suggested or SLOT_QUESTIONS[slot]

    return None


def needs_clarification(entities: list[str], constraints: dict) -> bool:
    """Clarification is required only when no entities were identified."""
    return not entities


async def resolve_question(
    user_text: str,
    intent_type: str,
    confidence: float,
    entities: list[str],
    constraints: dict,
    llm_suggested: Optional[str] = None,
    conversation: list[dict] | None = None,
    shopping_theme: Optional[str] = None,
    questions_asked: int = 0,
) -> Optional[str]:
    """
    Produce the clarification question using the dynamic context-aware system.

    Fallback chain:
        1. Dynamic LLM generator (full context — new system)
        2. Static slot-priority (this module — legacy)
        3. Static clarification_engine map (absolute fallback)

    Args:
        user_text: Original user input
        intent_type: Classified intent type
        confidence: Classification confidence
        entities: Extracted entities
        constraints: Constraints dict {quantity, budget, brand, diet, ...}
        llm_suggested: Question suggested by the initial LLM parse (may be None)
        conversation: Full Q→A history [{"question": ..., "answer": ...}, ...]
        shopping_theme: Identified shopping theme
        questions_asked: Number of questions already answered

    Returns:
        A clarification question string, or None when no clarification needed.
    """
    # Build context for the dynamic system
    context = ClarificationContext(
        original_query=user_text,
        intent_type=intent_type,
        confidence=confidence,
        shopping_theme=shopping_theme,
        entities=entities or [],
        constraints=constraints or {},
        conversation=conversation or [],
        questions_asked=questions_asked,
        max_questions=MAX_QUESTIONS,
    )

    # 1. Check stopping criteria first
    if should_stop(context):
        logger.info("Stopping criteria met in resolve_question — no more questions needed")
        return None

    # 2. Try dynamic LLM generator
    try:
        result = await generate_next_question(context)
        if result is not None:
            return result["question"]
        # LLM says sufficient context
        return None
    except Exception as exc:
        logger.warning("Dynamic clarification failed (%s) — using fallback", exc)

    # 3. Static slot-priority fallback
    q = next_question(entities, constraints, llm_suggested)
    if q is not None:
        return q

    if not needs_clarification(entities, constraints):
        return None

    # 4. Absolute fallback: static clarification_engine
    try:
        from app.services import clarification_engine

        smart = await clarification_engine.get_next_question_smart(
            user_text=user_text,
            intent_type=intent_type,
            confidence=confidence,
            entities=entities,
            previous_questions=[item.get("question", "") for item in (conversation or [])],
            answered_count=questions_asked,
        )
        if smart:
            return smart
        return clarification_engine.get_first_question(intent_type)
    except Exception as exc:
        logger.warning("Clarification fallback failed: %s", exc)
        return SLOT_QUESTIONS["entity"]
