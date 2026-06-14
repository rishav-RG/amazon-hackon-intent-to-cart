"""
Clarification Manager — priority-ordered slot checker.

Decides whether clarification is needed for a parsed shopping intent and
produces the next question by slot priority:

    1. missing entity
    2. quantity
    3. budget
    4. brand preference
    5. dietary restriction

Falls back to the existing clarification_engine (LLM smart question, then
static CLARIFICATION_MAP) when no specific slot question applies. Pure
composition — clarification_engine is not modified.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Static slot questions (used when the LLM did not supply one)
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

    Only the highest-priority MISSING slot drives a question. The 'entity'
    slot is mandatory; the others (quantity/budget/brand/diet) are treated as
    soft — we only ask for the single most important missing one.

    If the LLM already suggested a question, prefer it (it's context-aware).
    """
    constraints = constraints or {}

    # Mandatory: entity must be present
    if _slot_missing("entity", entities, constraints):
        return llm_suggested or SLOT_QUESTIONS["entity"]

    # Soft slots: ask for at most the single highest-priority missing one.
    # (Kept conservative so we don't over-question when entities are known.)
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
) -> Optional[str]:
    """
    Produce the clarification question, with graceful fallback chain:

        1. slot-priority question (this module)
        2. existing clarification_engine.get_next_question_smart (LLM)
        3. existing clarification_engine.get_first_question (static map)

    Returns None when no clarification is needed.
    """
    # 1. slot-priority
    q = next_question(entities, constraints, llm_suggested)
    if q is not None:
        return q

    if not needs_clarification(entities, constraints):
        return None

    # 2 + 3. delegate to existing engine (unchanged)
    try:
        from app.services import clarification_engine

        smart = await clarification_engine.get_next_question_smart(
            user_text=user_text,
            intent_type=intent_type,
            confidence=confidence,
            entities=entities,
            previous_questions=[],
            answered_count=0,
        )
        if smart:
            return smart
        return clarification_engine.get_first_question(intent_type)
    except Exception as exc:
        logger.warning("Clarification fallback failed: %s", exc)
        return SLOT_QUESTIONS["entity"]
