"""
SubstitutionEngine - Handles out-of-stock product replacement logic.

For each OOS product in a bundle:
- Queries the substitutions table by original_product_id
- If a row exists with confidence >= 0.85: auto-replace the item
- If confidence < 0.85: flag item (is_substituted=True, keep original)
- If no substitution found: leave as is (CheckoutService will handle final OOS block)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.substitution import Substitution
from app.schemas.bundle import BundleSchema, BundleItemSchema


# Confidence threshold for automatic replacement
CONFIDENCE_AUTO_REPLACE_THRESHOLD = 0.85


class SubstitutionEngine:
    """
    Applies product substitution logic to bundles based on inventory availability.
    
    This is a standalone lookup table (no FK relationships).
    Query pattern: WHERE original_product_id IN (...) ORDER BY confidence DESC
    """

    async def apply(
        self,
        bundles: list[BundleSchema],
        inventory_results: dict[str, dict],
        db: AsyncSession,
    ) -> list[BundleSchema]:
        """
        Applies substitution logic to each bundle in place.
        Returns the same bundle list with items mutated where needed.

        Args:
            bundles: BundleSchema objects from BundleGenerator.
            inventory_results: Output of InventoryAdapter.check_batch().
                              Format: { "prod-001": {"available": True, "warehouse": "WH-A"} }
            db: Async SQLAlchemy session.

        Returns:
            Same bundles list with OOS items substituted or flagged.
            
        Substitution Logic:
            - Available items: unchanged
            - OOS + no substitution: unchanged (flagged implicitly by OOS status)
            - OOS + high confidence (>= 0.85): auto-replace product_id, mark is_substituted=True
            - OOS + low confidence (< 0.85): mark is_substituted=True, keep original product_id
        """
        # Collect all OOS product_ids across all bundles to batch DB queries
        oos_product_ids = {
            item.product_id
            for bundle in bundles
            for item in bundle.items
            if not inventory_results.get(item.product_id, {}).get("available", True)
        }

        if not oos_product_ids:
            # No OOS items - return bundles unchanged
            return bundles

        # Fetch all relevant substitution rows in one query
        result = await db.execute(
            select(Substitution).where(
                Substitution.original_product_id.in_(oos_product_ids)
            )
        )
        all_subs = result.scalars().all()

        # Build lookup: original_product_id → best substitution row (highest confidence)
        best_sub: dict[str, Substitution] = {}
        for sub in all_subs:
            existing = best_sub.get(sub.original_product_id)
            if existing is None or sub.confidence > existing.confidence:
                best_sub[sub.original_product_id] = sub

        # Apply substitution logic to each bundle item
        for bundle in bundles:
            new_items: list[BundleItemSchema] = []
            
            for item in bundle.items:
                is_oos = not inventory_results.get(item.product_id, {}).get("available", True)

                if not is_oos:
                    # Item is available - no changes needed
                    new_items.append(item)
                    continue

                # Item is OOS - check for substitution
                sub = best_sub.get(item.product_id)

                if sub is None:
                    # No substitution found - leave item as is
                    # CheckoutService will block this at final hard check
                    new_items.append(item)
                    continue

                if sub.confidence >= CONFIDENCE_AUTO_REPLACE_THRESHOLD:
                    # High confidence - auto-replace the product
                    replaced = item.model_copy(update={
                        "product_id": sub.replacement_product_id,
                        "is_substituted": True,
                        "original_product_id": item.product_id,
                    })
                    new_items.append(replaced)
                else:
                    # Low confidence - flag only (keep original product_id)
                    flagged = item.model_copy(update={
                        "is_substituted": True,
                    })
                    new_items.append(flagged)

            # Replace bundle items with processed items
            bundle.items = new_items
            
            # Recalculate total price after substitutions
            bundle.total_price = sum(item.unit_price * item.quantity for item in bundle.items)

        return bundles
