"""
Gemini LLM Client for Intent-to-Cart backend.

Provides async LLM calls with:
- Redis caching of responses
- Configurable timeout (3s default)
- Graceful fallback on failure
- Structured JSON output parsing

Used by:
1. Intent classification fallback (when keyword confidence < 0.7)
2. Clarification question generation (contextual, not static)
"""

import asyncio
import hashlib
import json
import logging
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

LLM_TIMEOUT = 3.0  # seconds
LLM_CACHE_TTL = 3600  # 1 hour

_client_initialized = False


def _ensure_client():
    """Initialize the Gemini client with API key (lazy, once)."""
    global _client_initialized
    if not _client_initialized:
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not configured in settings")
        genai.configure(api_key=api_key)
        _client_initialized = True


def _make_cache_key(prefix: str, text: str) -> str:
    """Generate a cache key from prefix and text hash."""
    text_hash = hashlib.sha256(text.lower().strip().encode()).hexdigest()[:16]
    return f"{prefix}:{text_hash}"


async def _call_gemini(prompt: str, timeout: float = LLM_TIMEOUT) -> Optional[str]:
    """
    Call Gemini API with timeout. Returns raw text response or None on failure.
    
    Runs the synchronous genai call in a thread pool executor with asyncio timeout.
    """
    _ensure_client()

    def _sync_call():
        from app.config import settings
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temp for deterministic classification
                max_output_tokens=300,
            ),
        )
        return response.text

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_call),
            timeout=timeout,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("Gemini call timed out after %.1fs", timeout)
        return None
    except Exception as exc:
        logger.error("Gemini call failed: %s", exc)
        return None


def _parse_json_response(text: str) -> Optional[dict]:
    """Extract JSON from LLM response (handles markdown code fences)."""
    if not text:
        return None
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove first and last lines (```json and ```)
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    logger.warning("Failed to parse LLM JSON response: %s...", text[:100])
    return None


# ──────────────────────────────────────────────────────────────────────────────
# 1. Intent Classification via LLM
# ──────────────────────────────────────────────────────────────────────────────

INTENT_CLASSIFICATION_PROMPT = """You are an e-commerce shopping intent classifier.

Classify the following user text into EXACTLY ONE of these intent types:
- add_to_cart: User wants to add/buy/purchase products
- remove_from_cart: User wants to remove/delete items from cart
- search_product: User wants to find/browse/discover products
- reorder: User wants to buy same items as before
- substitute: User wants to replace a product with an alternative
- compare: User wants to compare products
- get_recommendation: User wants product suggestions/recommendations
- checkout: User wants to pay/complete/finalize their order

Also extract product-related entities (product names, categories, brands) from the text.

User text: "{text}"

Respond ONLY with valid JSON (no markdown, no explanation):
{{"intent_type": "one_of_the_8_types", "confidence": 0.0_to_1.0, "entities": ["entity1", "entity2"]}}"""


async def classify_intent_llm(text: str) -> Optional[dict]:
    """
    Classify user intent using Gemini LLM.
    
    Flow:
        1. Check Redis cache → return on hit
        2. Call Gemini with classification prompt (3s timeout)
        3. Parse JSON response
        4. Cache result → return
        5. On any failure → return None (caller uses keyword/semantic fallback)
    
    Returns:
        dict with {intent_type, confidence, entities} or None on failure.
    """
    cache_key = _make_cache_key("llm_intent", text)

    # Step 1: Check Redis cache
    try:
        cached = await cache_get(cache_key)
        if cached is not None:
            logger.debug("LLM intent cache hit: %s", cache_key)
            cached["cache_hit"] = True
            return cached
    except Exception as exc:
        logger.warning("LLM intent cache read failed: %s", exc)

    # Step 2: Call Gemini
    prompt = INTENT_CLASSIFICATION_PROMPT.format(text=text)
    raw_response = await _call_gemini(prompt)

    if raw_response is None:
        return None

    # Step 3: Parse response
    result = _parse_json_response(raw_response)
    if result is None:
        return None

    # Validate required fields
    valid_intents = [
        "add_to_cart", "remove_from_cart", "search_product", "reorder",
        "substitute", "compare", "get_recommendation", "checkout",
    ]
    if result.get("intent_type") not in valid_intents:
        logger.warning("LLM returned invalid intent_type: %s", result.get("intent_type"))
        return None

    # Normalize confidence
    confidence = float(result.get("confidence", 0.7))
    confidence = max(0.0, min(1.0, confidence))
    result["confidence"] = confidence
    result["method"] = "llm"

    # Ensure entities is a list
    if not isinstance(result.get("entities"), list):
        result["entities"] = []

    # Step 4: Cache result
    try:
        await cache_set(cache_key, result, LLM_CACHE_TTL)
    except Exception as exc:
        logger.warning("LLM intent cache write failed: %s", exc)

    result["cache_hit"] = False
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 2. Clarification Question Generation via LLM
# ──────────────────────────────────────────────────────────────────────────────

CLARIFICATION_PROMPT = """You are a helpful shopping assistant for an Indian grocery e-commerce app.

A user said: "{user_text}"
We classified their intent as: {intent_type} (confidence: {confidence})
Shopping theme: {shopping_theme}
Entities detected: {entities}
Constraints collected: {constraints}
Conversation so far:
{conversation_history}

Generate the next clarification question to better understand what the user needs.
The question should:
- Be short and conversational (max 15 words)
- NOT repeat anything already covered by the entities, constraints, or previous answers
- Focus on the most important missing information for product retrieval
- Be specific to what the user said and their shopping theme

Respond ONLY with valid JSON (no markdown):
{{"question": "your question here"}}"""


async def generate_clarification_question(
    user_text: str,
    intent_type: str,
    confidence: float,
    entities: list[str],
    previous_questions: list[str],
    previous_answers: list[str] | None = None,
    shopping_theme: str | None = None,
    constraints: dict | None = None,
) -> Optional[str]:
    """
    Generate a contextual clarification question using Gemini.
    
    Falls back to None if LLM fails (caller uses static CLARIFICATION_MAP).
    
    Args:
        user_text: Original user input
        intent_type: Classified intent type
        confidence: Classification confidence
        entities: Extracted entities from the text
        previous_questions: Questions already asked in this session
        previous_answers: Answers to previous questions (paired with previous_questions)
        shopping_theme: Identified shopping theme (e.g., biryani_ingredients)
        constraints: Constraints collected so far {quantity, budget, brand, diet}
        
    Returns:
        A clarification question string, or None on failure.
    """
    # Build cache key from all relevant context
    context_str = f"{user_text}|{intent_type}|{len(previous_questions)}|{shopping_theme}"
    cache_key = _make_cache_key("llm_clarify", context_str)

    # Check cache
    try:
        cached = await cache_get(cache_key)
        if cached is not None:
            return cached.get("question")
    except Exception:
        pass

    # Format conversation history
    conversation_lines = []
    if previous_questions and previous_answers:
        for i, (q, a) in enumerate(zip(previous_questions, previous_answers), 1):
            conversation_lines.append(f"  Q{i}: {q}")
            conversation_lines.append(f"  A{i}: {a}")
    elif previous_questions:
        for i, q in enumerate(previous_questions, 1):
            conversation_lines.append(f"  Q{i}: {q}")
    conversation_str = "\n".join(conversation_lines) if conversation_lines else "  (first question)"

    # Format constraints
    constraints_str = "none"
    if constraints:
        filled = {k: v for k, v in constraints.items() if v is not None}
        if filled:
            constraints_str = ", ".join(f"{k}={v}" for k, v in filled.items())

    # Build prompt
    prompt = CLARIFICATION_PROMPT.format(
        user_text=user_text,
        intent_type=intent_type,
        confidence=confidence,
        shopping_theme=shopping_theme or "not identified",
        entities=", ".join(entities) if entities else "none",
        constraints=constraints_str,
        conversation_history=conversation_str,
    )

    # Call Gemini
    raw_response = await _call_gemini(prompt, timeout=2.0)

    if raw_response is None:
        return None

    # Parse response
    result = _parse_json_response(raw_response)
    if result is None or "question" not in result:
        # Try to use raw text as question if it's short enough
        cleaned = raw_response.strip().strip('"')
        if 5 < len(cleaned) < 100 and "?" in cleaned:
            question = cleaned
        else:
            return None
    else:
        question = result["question"]

    # Cache the question
    try:
        await cache_set(cache_key, {"question": question}, LLM_CACHE_TTL)
    except Exception:
        pass

    return question


# ──────────────────────────────────────────────────────────────────────────────
# 3. Hybrid Structured Shopping-Intent Parser (NEW)
# ──────────────────────────────────────────────────────────────────────────────

# The LLM acts as a STRUCTURED PARSER, not an open-ended intent discoverer.
# It may only return one of these 5 intent types and a generic shopping_theme.
SHOPPING_PARSER_PROMPT = """You are a structured shopping-intent parser for an e-commerce app.

Parse the user's message into a strict JSON object. Do not invent product
catalog categories. You may only output a GENERIC shopping_theme phrase
(examples: morning_meal, protein_diet, movie_night, hostel_monthly,
birthday_party, baby_essentials, pet_supplies, home_cleaning, daily_grooming).

intent_type MUST be EXACTLY ONE of:
- search_product: user wants to find/browse products
- recommendation_request: user wants suggestions/recommendations
- add_to_cart: user wants to add/buy specific products
- build_bundle: user wants a themed set/kit/bundle of products
- compare_products: user wants to compare products

Extract product entities (concrete nouns) and constraints.
Set needs_clarification=true ONLY if you cannot identify any entities AND no
usable shopping_theme.

User message: "{text}"

Respond ONLY with valid JSON (no markdown, no commentary):
{{"intent_type": "one_of_the_5_types",
"confidence": 0.0_to_1.0,
"shopping_theme": "generic_theme_or_null",
"entities": ["entity1", "entity2"],
"constraints": {{"quantity": null, "budget": null, "brand": null, "diet": null}},
"needs_clarification": false,
"clarification_question": null}}"""

_VALID_PARSER_INTENTS = {
    "search_product",
    "recommendation_request",
    "add_to_cart",
    "build_bundle",
    "compare_products",
}


async def parse_shopping_intent_llm(text: str) -> Optional[dict]:
    """
    Parse a shopping message into a structured slot object via Gemini.

    Reuses _call_gemini(), _parse_json_response(), Redis caching, and timeout.

    Returns a dict with keys:
        intent_type, confidence, shopping_theme, entities,
        constraints{quantity,budget,brand,diet}, needs_clarification,
        clarification_question
    or None on any failure (caller falls back to keyword/semantic path).
    """
    cache_key = _make_cache_key("llm_parse", text)

    # Step 1: cache
    try:
        cached = await cache_get(cache_key)
        if cached is not None:
            cached["cache_hit"] = True
            return cached
    except Exception as exc:
        logger.warning("Shopping-parse cache read failed: %s", exc)

    # Step 2: call Gemini
    prompt = SHOPPING_PARSER_PROMPT.format(text=text)
    raw_response = await _call_gemini(prompt)
    if raw_response is None:
        return None

    # Step 3: parse + validate
    result = _parse_json_response(raw_response)
    if result is None:
        return None

    if result.get("intent_type") not in _VALID_PARSER_INTENTS:
        logger.warning("Parser returned invalid intent_type: %s", result.get("intent_type"))
        return None

    # Normalize fields
    confidence = float(result.get("confidence", 0.7))
    result["confidence"] = max(0.0, min(1.0, confidence))

    if not isinstance(result.get("entities"), list):
        result["entities"] = []

    theme = result.get("shopping_theme")
    if isinstance(theme, str) and theme.strip().lower() in ("", "null", "none"):
        theme = None
    result["shopping_theme"] = theme

    constraints = result.get("constraints")
    if not isinstance(constraints, dict):
        constraints = {}
    result["constraints"] = {
        "quantity": constraints.get("quantity"),
        "budget": constraints.get("budget"),
        "brand": constraints.get("brand"),
        "diet": constraints.get("diet"),
    }

    result["needs_clarification"] = bool(result.get("needs_clarification", False))
    result.setdefault("clarification_question", None)
    result["method"] = "llm_parser"

    # Step 4: cache
    try:
        await cache_set(cache_key, result, LLM_CACHE_TTL)
    except Exception as exc:
        logger.warning("Shopping-parse cache write failed: %s", exc)

    result["cache_hit"] = False
    return result
