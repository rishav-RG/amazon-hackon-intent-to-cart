"""Bundle context builder.

Builds a normalized, bundle-ready context from the persisted intent and the
ordered clarification answers.
"""

from __future__ import annotations

import logging
import re

from app.models.intent import Intent_Model
from app.schemas.bundle_context import BundleContext, ConfirmedEntity, ShoppingConstraints
from app.services.category_resolver import resolve

logger = logging.getLogger(__name__)


class BundleContextBuilder:
    @staticmethod
    def _normalize_text(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _extract_quantity(value: str) -> int | None:
        match = re.search(r"\b(\d+)\b", value)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _extract_budget(value: str) -> float | None:
        match = re.search(r"\b(\d+(?:\.\d+)?)\b", value)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _merge_constraints(
        intent_constraints: dict | None,
        clarifications: list[dict],
    ) -> ShoppingConstraints:
        merged = ShoppingConstraints(**(intent_constraints or {}))

        for item in clarifications:
            question = (item.get("question") or "").lower()
            answer = (item.get("answer") or "").strip()
            if not answer:
                continue

            if merged.quantity is None and ("how many" in question or "quantity" in question):
                quantity = BundleContextBuilder._extract_quantity(answer)
                if quantity is not None:
                    merged.quantity = quantity
                    continue

            if merged.budget is None and ("budget" in question or "price" in question):
                budget = BundleContextBuilder._extract_budget(answer)
                if budget is not None:
                    merged.budget = budget
                    continue

            if merged.brand is None and "brand" in question:
                merged.brand = answer
                continue

            if merged.diet is None and ("diet" in question or "vegetarian" in question or "vegan" in question):
                merged.diet = answer

        return merged

    @staticmethod
    def _build_confirmed_entities(
        entities: list[str],
        clarifications: list[dict],
        constraints: ShoppingConstraints,
    ) -> list[ConfirmedEntity]:
        quantity_answers = [
            BundleContextBuilder._extract_quantity(item.get("answer", "") or "")
            for item in clarifications
        ]
        quantity_answers = [value for value in quantity_answers if value is not None]

        confirmed_entities: list[ConfirmedEntity] = []
        for index, entity in enumerate(entities):
            quantity = quantity_answers[index] if index < len(quantity_answers) else constraints.quantity
            confirmed_entities.append(
                ConfirmedEntity(
                    raw=entity,
                    canonical=BundleContextBuilder._normalize_text(entity),
                    brand=constraints.brand,
                    quantity=quantity,
                    unit="items" if quantity is not None else "units",
                )
            )
        return confirmed_entities

    @staticmethod
    def _build_semantic_query(
        intent: Intent_Model,
        clarifications: list[dict],
        confirmed_entities: list[ConfirmedEntity],
        constraints: ShoppingConstraints,
    ) -> str:
        tokens: list[str] = []

        if constraints.brand:
            tokens.append(constraints.brand)

        tokens.extend(entity.raw for entity in confirmed_entities)

        for item in clarifications:
            answer = (item.get("answer") or "").strip()
            if answer:
                tokens.append(answer)

        if intent.shopping_theme:
            tokens.append(intent.shopping_theme.replace("_", " "))

        deduped: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            normalized = token.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(token.strip())

        return " ".join(deduped)

    @staticmethod
    def _build_category_query(intent: Intent_Model, resolved_category: str) -> str:
        parts = resolved_category.replace("_", " ").split()
        if intent.shopping_theme:
            parts.extend(intent.shopping_theme.replace("_", " ").split())
        if not parts:
            parts = [intent.intent_type.replace("_", " ")]
        return " ".join(dict.fromkeys(part for part in parts if part))

    @staticmethod
    async def build(intent: Intent_Model, clarifications: list[dict]) -> BundleContext:
        """Consolidate intent data and clarification answers into a final BundleContext."""
        intent_entities = list(intent.entities or [])
        intent_constraints = intent.constraints or {}
        constraints = BundleContextBuilder._merge_constraints(intent_constraints, clarifications)
        resolved_category = resolve(intent.shopping_theme) if intent.shopping_theme else intent.intent_type
        confirmed_entities = BundleContextBuilder._build_confirmed_entities(
            intent_entities,
            clarifications,
            constraints,
        )

        product_query_hints: list[str] = []
        for hint in [
            *(entity.raw for entity in confirmed_entities),
            *(constraints.brand and [constraints.brand] or []),
            *(intent.shopping_theme and intent.shopping_theme.replace("_", " ").split() or []),
        ]:
            normalized = hint.strip()
            if normalized and normalized not in product_query_hints:
                product_query_hints.append(normalized)

        return BundleContext(
            intent_id=str(intent.id),
            intent_type=intent.intent_type,
            shopping_theme=intent.shopping_theme,
            resolved_category=resolved_category,
            confirmed_entities=confirmed_entities,
            constraints=constraints,
            semantic_query=BundleContextBuilder._build_semantic_query(
                intent,
                clarifications,
                confirmed_entities,
                constraints,
            ),
            category_query=BundleContextBuilder._build_category_query(intent, resolved_category),
            product_query_hints=product_query_hints,
        )