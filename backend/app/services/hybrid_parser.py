"""
Hybrid Parser — Intent Parser stage of the hybrid intent-to-cart pipeline.

Wraps the LLM structured parser (parse_shopping_intent_llm) with a guaranteed
fallback to the existing deterministic classifier (classify_hybrid).

Contract:
    parse(text) -> HybridParseResult   (NEVER raises; always returns a result)

If the LLM parser succeeds, we get rich slots (theme, entities, constraints).
If it fails (quota/timeout/error), we degrade to classify_hybrid() and return
a result with shopping_theme=None — which downstream treats exactly like the
current MOCK_CATALOG behavior.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.schemas.intent import PARSER_TO_INTENT
from app.services import intent_engine

logger = logging.getLogger(__name__)


@dataclass
class HybridParseResult:
    """Normalized result of the Intent Parser stage."""

    intent_type: str                      # mapped to existing 8-value enum
    confidence: float
    entities: list[str] = field(default_factory=list)
    shopping_theme: Optional[str] = None
    constraints: dict = field(default_factory=dict)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    llm_used: bool = False
    fallback: bool = False


def _empty_constraints() -> dict:
    return {"quantity": None, "budget": None, "brand": None, "diet": None}


async def parse(text: str) -> HybridParseResult:
    """
    Parse user text into a HybridParseResult.

    Order:
        1. Try LLM structured parser (parse_shopping_intent_llm)
           → map parser intent_type to existing enum via PARSER_TO_INTENT
        2. On None/failure → fall back to intent_engine.classify_hybrid()
           → shopping_theme=None, empty constraints (current behavior)
    """
    # ── 1. LLM structured parse ──
    try:
        from app.services.llm_client import parse_shopping_intent_llm

        parsed = await parse_shopping_intent_llm(text)
        if parsed is not None:
            parser_intent = parsed.get("intent_type")
            mapped_intent = PARSER_TO_INTENT.get(parser_intent, "search_product")
            return HybridParseResult(
                intent_type=mapped_intent,
                confidence=float(parsed.get("confidence", 0.7)),
                entities=parsed.get("entities", []) or [],
                shopping_theme=parsed.get("shopping_theme"),
                constraints=parsed.get("constraints") or _empty_constraints(),
                needs_clarification=bool(parsed.get("needs_clarification", False)),
                clarification_question=parsed.get("clarification_question"),
                llm_used=True,
                fallback=False,
            )
        logger.info("LLM parser returned None — falling back to classify_hybrid")
    except Exception as exc:
        logger.warning("LLM parser error (%s) — falling back to classify_hybrid", exc)

    # ── 2. Deterministic fallback (existing behavior) ──
    base = await intent_engine.classify_hybrid(text)
    return HybridParseResult(
        intent_type=base.intent_type,
        confidence=base.confidence,
        entities=base.entities,
        shopping_theme=None,                 # → downstream uses MOCK_CATALOG path
        constraints=_empty_constraints(),
        needs_clarification=base.confidence < 0.7,
        clarification_question=None,
        llm_used=base.llm_used,
        fallback=True,
    )
