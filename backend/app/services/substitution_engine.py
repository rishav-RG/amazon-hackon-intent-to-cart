"""
SubstitutionEngine for Intent-to-Cart backend.

Handles automatic product substitution for out-of-stock items using
database-driven substitution mappings.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.substitution import Substitution_Model
from app.schemas.bundle import BundleSchema


class SubstitutionEngine:
    """
    Applies product substitutions for out-of-stock items in bundles.
    
    Key Behaviors (Phase 0 Adaptation):
        - NO confidence threshold (Substitution_Model lacks confidence field)
        - ALL found substitutions are auto-applied
        - OOS items without substitution are flagged but NOT removed
        - Substitution metadata stored in schema only (not DB)
    """
    
    @staticmethod
    async def apply(
        bundles: list[BundleSchema],
        db: AsyncSession
    ) -> list[BundleSchema]:
        """
        Apply substitutions to out-of-stock items in bundles.
        
        Args:
            bundles: List of bundles with inventory data populated.
            db: Async database session.
            
        Returns:
            Bundles with substitutions applied in-place.
            
        Algorithm:
            1. Identify OOS items (warehouse == "")
            2. Query Substitution_Model for replacements
            3. Auto-replace ALL found substitutions (no confidence check)
            4. Update BundleItemSchema fields:
               - is_substituted = True
               - original_product_id = original product
               - product_id = replacement product
            5. Keep OOS items without substitution (flagged for user awareness)
            
        Note:
            - Substitution metadata NOT persisted to DB (schema-only)
            - Items remain in bundle even if no substitution found
            - Requires bundles to have inventory data (warehouse field)
        """
        # Collect all OOS product IDs across all bundles
        oos_product_ids = set()
        for bundle in bundles:
            for item in bundle.items:
                # OOS items have empty warehouse
                if not item.warehouse:
                    oos_product_ids.add(item.product_id)
        
        if not oos_product_ids:
            # No OOS items, return bundles unchanged
            return bundles
        
        # Query substitutions for OOS products
        result = await db.execute(
            select(Substitution_Model).where(
                Substitution_Model.original_product_id.in_(oos_product_ids)
            )
        )
        substitutions = result.scalars().all()
        
        # Build substitution map: original_id -> replacement_id
        substitution_map = {
            sub.original_product_id: sub.replacement_product_id
            for sub in substitutions
        }
        
        # Apply substitutions to all bundles
        for bundle in bundles:
            for item in bundle.items:
                # Check if item is OOS and has a substitution
                if not item.warehouse and item.product_id in substitution_map:
                    # Auto-replace (no confidence threshold in model)
                    original_product_id = item.product_id
                    replacement_product_id = substitution_map[original_product_id]
                    
                    # Update item in-place
                    item.is_substituted = True
                    item.original_product_id = original_product_id
                    item.product_id = replacement_product_id
                    
                    # Note: Product metadata (name, brand, price) would need
                    # to be updated from catalog in production.
                    # For Phase 3, we keep original metadata and mark substituted.
                    # Phase 4 router will handle full metadata refresh.
        
        return bundles
