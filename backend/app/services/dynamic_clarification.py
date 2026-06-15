"""
Dynamic Clarification Generator — Context-aware question generation.

Replaces the static slot-priority approach with an LLM-driven system that:
1. Considers full conversation history (questions + answers)
2. Checks stopping criteria before generating the next question
3. Reserves mandatory slots (quantity + budget) for final question slots
4. Never re-asks information already provided
5. Generates questions specific to the shopping theme and accumulated context

Usage:
    from app.services.dynamic_clarification import generate_next_question, should_stop

    context = ClarificationContext(...)
    if should_stop(context):
        return None  # proceed to bundle generation
    result = await generate_next_question(context)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

MAX_QUESTIONS = 5


# ──────────────────────────────────────────────────────────────────────────────
# Context Model
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ClarificationContext:
    """Accumulated state for dynamic clarification generation."""

    # Original intent parse
    original_query: str
    intent_type: str
    confidence: float
    shopping_theme: Optional[str] = None
    entities: list[str] = field(default_factory=list)

    # Constraints collected so far (from parse + answers)
    constraints: dict = field(default_factory=dict)

    # Full conversation history (ordered Q→A pairs)
    conversation: list[dict] = field(default_factory=list)

    # Tracking
    questions_asked: int = 0
    max_questions: int = MAX_QUESTIONS


# ──────────────────────────────────────────────────────────────────────────────
# Stopping Criteria
# ──────────────────────────────────────────────────────────────────────────────

def _has_quantity(constraints: dict) -> bool:
    """Check if quantity/serving info is available."""
    return (
        constraints.get("quantity") is not None
        or constraints.get("serving_size") is not None
    )


def _has_budget(constraints: dict) -> bool:
    """Check if budget/price info is available."""
    return constraints.get("budget") is not None


def should_stop(context: ClarificationContext) -> bool:
    """
    Determine if enough information has been collected to proceed to
    retrieval and bundle generation.

    Returns True when ANY of these conditions are met:
    1. Hard cap: questions_asked >= max_questions (5)
    2. All three mandatory slots filled: entities/theme + quantity + budget
    3. High-confidence initial parse: confidence >= 0.9 with entities + theme
    
    MANDATORY constraints (all three required before stopping):
    - Entity/product specificity: entities >= 1 OR shopping_theme is set
    - Quantity/serving size
    - Budget/price range
    """
    c = context.constraints
    has_qty = _has_quantity(c)
    has_bgt = _has_budget(c)
    has_entities = len(context.entities) >= 1
    has_theme = context.shopping_theme is not None
    has_product_context = has_entities or has_theme

    # 1. Hard cap
    if context.questions_asked >= context.max_questions:
        return True

    # 2. All THREE mandatory slots filled
    if has_qty and has_bgt and has_product_context:
        return True

    # 3. High confidence initial parse with rich context
    if context.confidence >= 0.9 and len(context.entities) >= 2 and has_theme:
        return True

    return False


# ──────────────────────────────────────────────────────────────────────────────
# Mandatory Slot Reservation
# ──────────────────────────────────────────────────────────────────────────────

def _get_mandatory_fallback(context: ClarificationContext) -> Optional[str]:
    """
    Force-ask mandatory constraints when they're missing.

    Mandatory constraints (in priority order):
    1. Entity/product specificity — ALWAYS ask first if missing (regardless of remaining slots)
    2. Quantity / serving size — ask when ≤ 2 slots remain OR entity is filled
    3. Budget / price range — ask when ≤ 2 slots remain OR entity+quantity filled

    This ensures the system never proceeds to retrieval without knowing
    WHAT the user wants, HOW MUCH, and their BUDGET.
    """
    remaining = context.max_questions - context.questions_asked
    c = context.constraints
    has_entities = len(context.entities) >= 1
    has_theme = context.shopping_theme is not None
    has_product_context = has_entities or has_theme

    # Priority 1: ALWAYS ask what the user wants if we don't know
    if not has_product_context:
        return "What specific products or items are you looking for?"

    # Priority 2: Quantity — force when remaining ≤ 2 OR when we have product context
    if not _has_quantity(c) and (remaining <= 2 or has_product_context):
        if context.shopping_theme and "ingredient" in (context.shopping_theme or ""):
            return "How many people are you planning to serve?"
        return "How much quantity do you need?"

    # Priority 3: Budget — force when remaining ≤ 2 OR when we have product+quantity
    if not _has_budget(c) and (remaining <= 2 or (_has_quantity(c) and has_product_context)):
        return "Do you have a budget or price range in mind?"

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Context Merging
# ──────────────────────────────────────────────────────────────────────────────

def merge_answer_into_constraints(
    constraints: dict,
    question: str,
    answer: str,
) -> dict:
    """
    Extract constraint values from a clarification answer and merge into
    the existing constraints dict. Returns updated copy.
    """
    updated = dict(constraints)
    q_lower = (question or "").lower()
    a_lower = (answer or "").strip().lower()
    answer_stripped = (answer or "").strip()

    if not answer_stripped:
        return updated

    # Quantity extraction
    if updated.get("quantity") is None and (
        "how many" in q_lower
        or "quantity" in q_lower
        or "how much" in q_lower
        or "serve" in q_lower
        or "people" in q_lower
    ):
        match = re.search(r"\b(\d+)\b", answer_stripped)
        if match:
            updated["quantity"] = int(match.group(1))
            return updated
        # Also handle serving_size
        updated["serving_size"] = answer_stripped

    # Budget extraction
    if updated.get("budget") is None and (
        "budget" in q_lower or "price" in q_lower or "spend" in q_lower or "range" in q_lower
    ):
        match = re.search(r"\b(\d+(?:\.\d+)?)\b", answer_stripped)
        if match:
            updated["budget"] = float(match.group(1))
            return updated

    # Brand extraction
    if updated.get("brand") is None and "brand" in q_lower:
        updated["brand"] = answer_stripped
        return updated

    # Diet extraction
    if updated.get("diet") is None and (
        "diet" in q_lower
        or "vegetarian" in q_lower
        or "veg" in q_lower
        or "non-veg" in q_lower
        or "preference" in q_lower
    ):
        updated["diet"] = answer_stripped
        return updated

    # Generic: if the answer mentions veg/non-veg anywhere
    if updated.get("diet") is None and (
        "vegetarian" in a_lower or "non-veg" in a_lower or "vegan" in a_lower
    ):
        updated["diet"] = answer_stripped

    return updated


def extract_entities_from_answer(answer: str, existing_entities: list[str]) -> list[str]:
    """Extract potential new entities from a clarification answer.
    
    Handles comma-separated lists and common product names.
    """
    # Common stop words that aren't product entities
    stop_words = {
        "want", "need", "like", "would", "please", "about", "around",
        "prefer", "looking", "something", "anything", "good", "best",
        "have", "with", "from", "that", "this", "some", "also", "just",
        "maybe", "think", "know", "sure", "okay", "yeah", "yes", "no",
        "for", "and", "the", "not", "any", "but", "few", "lot", "many",
        "more", "less", "much", "very", "really", "quite", "only",
    }
    
    existing_lower = {e.lower() for e in existing_entities}
    new_entities = []
    
    # Split by commas first to handle "chips, namkeen, biscuits"
    parts = [p.strip() for p in answer.replace(" and ", ",").split(",")]
    
    for part in parts:
        # Clean the part
        cleaned = part.strip().strip(",.!?;:")
        if not cleaned:
            continue
        
        # If the whole comma-separated chunk looks like a product name
        words = cleaned.split()
        # Filter out pure stop words
        meaningful_words = [w for w in words if w.lower() not in stop_words and len(w) > 1]
        
        if meaningful_words:
            entity = " ".join(meaningful_words)
            if entity.lower() not in existing_lower and len(entity) > 2:
                new_entities.append(entity)
                existing_lower.add(entity.lower())
    
    return new_entities


# ──────────────────────────────────────────────────────────────────────────────
# Dynamic Question Generation (LLM)
# ──────────────────────────────────────────────────────────────────────────────

DYNAMIC_CLARIFICATION_PROMPT = """You are a contextual shopping assistant for an Indian grocery e-commerce app.

Your job: determine the SINGLE most valuable piece of missing information to ask the user, given everything collected so far.

=== CONTEXT ===
Original query: "{original_query}"
Intent type: {intent_type}
Shopping theme: {shopping_theme}
Entities identified: {entities}

Constraints collected so far:
{constraints_yaml}

Conversation history:
{conversation_history}

Questions asked so far: {questions_asked}/{max_questions}

=== RULES ===
1. NEVER ask for information already provided in entities, constraints, or previous answers.
2. Prioritize questions that improve product retrieval and bundle quality.
3. Quantity/units and budget are MANDATORY — if not yet collected and ≤2 slots remain, ask for one of these.
4. Ask ONE question. Keep it short (≤15 words), conversational, specific to the user's shopping context.
5. If sufficient context exists for a good product search, respond with {{"question": null, "slot": "none", "reason": "sufficient_context"}}.
6. NEVER repeat a question semantically similar to one already asked.

=== PRIORITY ORDER ===
- What specific items/variants are needed (if entities are vague or empty)
- Key attribute that narrows search (serving size for recipes, veg/non-veg for food, age for baby items)
- Quantity / how much / how many
- Budget / price range
- Brand preference (only if relevant and not already stated)
- Dietary restrictions (only if relevant to food items)

=== OUTPUT ===
Respond ONLY with valid JSON (no markdown, no commentary):
{{"question": "your question here or null", "slot": "which_slot_this_fills", "reason": "brief_reason"}}"""


def _format_constraints(constraints: dict) -> str:
    """Format constraints as readable YAML-like text."""
    if not constraints:
        return "  (none collected yet)"
    lines = []
    for key, value in constraints.items():
        if value is not None:
            lines.append(f"  {key}: {value}")
    return "\n".join(lines) if lines else "  (none collected yet)"


def _format_conversation(conversation: list[dict]) -> str:
    """Format conversation history as readable text."""
    if not conversation:
        return "  (no conversation yet — this is the first question)"
    lines = []
    for i, turn in enumerate(conversation, 1):
        q = turn.get("question", "")
        a = turn.get("answer", "")
        lines.append(f"  Q{i}: {q}")
        lines.append(f"  A{i}: {a}")
    return "\n".join(lines)


async def generate_next_question(context: ClarificationContext) -> Optional[dict]:
    """
    Generate the next clarification question using full accumulated context.

    Returns:
        {"question": str, "slot": str} or None if sufficient context / LLM says stop.

    Flow:
    1. Check stopping criteria → return None if satisfied
    2. Check mandatory slot reservation (≤2 remaining → force quantity/budget)
    3. Call LLM with full accumulated context
    4. Parse and validate response
    5. Return question dict or None
    """
    # 1. Stopping criteria
    if should_stop(context):
        logger.info("Stopping criteria met — clarification complete")
        return None

    # 2. Mandatory slot reservation
    mandatory = _get_mandatory_fallback(context)
    if mandatory:
        slot = "quantity" if not _has_quantity(context.constraints) else "budget"
        logger.info("Mandatory slot reservation: asking for %s", slot)
        return {"question": mandatory, "slot": slot}

    # 3. LLM call with full context
    try:
        from app.services.llm_client import _call_gemini, _parse_json_response

        prompt = DYNAMIC_CLARIFICATION_PROMPT.format(
            original_query=context.original_query,
            intent_type=context.intent_type,
            shopping_theme=context.shopping_theme or "not identified",
            entities=", ".join(context.entities) if context.entities else "none detected",
            constraints_yaml=_format_constraints(context.constraints),
            conversation_history=_format_conversation(context.conversation),
            questions_asked=context.questions_asked,
            max_questions=context.max_questions,
        )

        raw_response = await _call_gemini(prompt, timeout=2.5)

        if raw_response is None:
            logger.warning("LLM returned None for dynamic clarification")
            return _static_fallback(context)

        result = _parse_json_response(raw_response)
        if result is None:
            logger.warning("Failed to parse LLM dynamic clarification response")
            return _static_fallback(context)

        question = result.get("question")
        if question is None:
            # LLM says sufficient context
            logger.info("LLM determined sufficient context: %s", result.get("reason"))
            return None

        slot = result.get("slot", "unknown")
        return {"question": question, "slot": slot}

    except Exception as exc:
        logger.error("Dynamic clarification LLM error: %s", exc)
        return _static_fallback(context)


# ──────────────────────────────────────────────────────────────────────────────
# Static Fallback
# ──────────────────────────────────────────────────────────────────────────────

_FALLBACK_QUESTIONS = {
    "add_to_cart": [
        "What specific product are you looking for?",
        "How many units would you like?",
        "Do you have a preferred brand?",
        "What's your budget for this?",
        "Any other preferences?",
    ],
    "search_product": [
        "What category does the product belong to?",
        "How much quantity do you need?",
        "Do you have a price range in mind?",
        "Any preferred brand?",
        "Any specific features you need?",
    ],
    "get_recommendation": [
        "What type of product are you looking for?",
        "How many do you need?",
        "What's your budget?",
        "Is this for personal use or a gift?",
        "Any brand preference?",
    ],
}


def _static_fallback(context: ClarificationContext) -> Optional[dict]:
    """
    Fallback to a static question when LLM is unavailable.
    Follows mandatory priority: entity → quantity → budget.
    """
    has_entities = len(context.entities) >= 1
    has_theme = context.shopping_theme is not None

    # Priority 1: Must know what the user wants
    if not has_entities and not has_theme:
        return {"question": "What specific products or items are you looking for?", "slot": "entity"}

    # Priority 2: Quantity
    if not _has_quantity(context.constraints):
        return {"question": "How much quantity do you need?", "slot": "quantity"}

    # Priority 3: Budget
    if not _has_budget(context.constraints):
        return {"question": "Do you have a budget in mind?", "slot": "budget"}

    # Additional context questions from static map
    questions = _FALLBACK_QUESTIONS.get(context.intent_type, _FALLBACK_QUESTIONS["search_product"])
    idx = context.questions_asked
    if idx < len(questions):
        return {"question": questions[idx], "slot": "general"}

    return None
