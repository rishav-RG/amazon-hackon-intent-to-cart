"""
Bundle generation router for Intent-to-Cart backend.

Provides GET /v1/bundles/{intent_id} endpoint that orchestrates the complete
bundle generation pipeline: personalization, generation, inventory, ETA,
substitution, ranking, persistence, caching, and events.

Phase 4 integration of all Dev B services.
"""

import hashlib
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user_id
from app.events import emit
from app.exceptions import AppException, INTENT_NOT_FOUND
from app.models.bundle import Bundle_Model, BundleItem
from app.models.intent import Intent_Model
from app.schemas.bundle_context import BundleContext
from app.schemas.bundle import BundleListResponse
from app.services.personalization_service import PersonalizationService
from app.services.bundle_generator import BundleGenerator
from app.services.ranking_engine import RankingEngine
from app.services.substitution_engine import SubstitutionEngine
from app.services import category_resolver, product_retriever
from app.adapters.inventory_adapter import InventoryAdapter
from app.adapters.eta_adapter import ETAAdapter
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["bundles"])


@router.get("/bundles/{intent_id}", response_model=BundleListResponse)
async def get_bundles(
    intent_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> BundleListResponse:
    """
    Get ranked product bundles for a classified intent.
    
    12-Step Pipeline:
    1. Fetch Intent from DB (validate exists)
    2. Redis cache check (key: bundle:{intent_type}:{user_id_hash})
    3. Get personalization signals
    4. Generate 3 bundles (budget, classic, premium)
    5. Check inventory for all products
    6. Check ETA for all products
    7. Apply substitutions for OOS items
    8. Rank bundles by weighted score
    9. Persist bundles to DB
    10. Cache result in Redis (TTL from config)
    11. Emit bundle.generated event
    12. Return response with recommended + all options
    
    Args:
        intent_id: UUID of the classified intent.
        user_id: Current user ID (from auth header).
        db: Database session.
        
    Returns:
        BundleListResponse with recommended bundle and all options.
        
    Raises:
        HTTPException 404: Intent not found.
        HTTPException 500: Internal errors during processing.
    """
    # Step 1: Fetch Intent from DB
    result = await db.execute(
        select(Intent_Model).where(Intent_Model.id == intent_id)
    )
    intent = result.scalar_one_or_none()
    
    if not intent:
        raise AppException(
            error_code=INTENT_NOT_FOUND[0],
            message=f"Intent with ID {intent_id} not found",
            status_code=INTENT_NOT_FOUND[1]
        )

    # Verify intent belongs to user
    if intent.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Intent belongs to different user"
        )

    intent_type = intent.intent_type
    shopping_theme = getattr(intent, "shopping_theme", None)
    intent_entities = getattr(intent, "entities", None) or []
    intent_constraints = getattr(intent, "constraints", None) or {}

    # ── Clarification Context / Hybrid Retrieval Layer ──
    # Priority:
    # 1. Use enriched clarification bundle context if available
    # 2. Fall back to original shopping_theme retrieval logic
    # 3. Fall back to MOCK_CATALOG

    resolved_category = None
    retrieved_products = None
    bundle_context = None

    try:
        # Check for enriched clarification bundle context
        bundle_context_raw = await cache_get(
            f"bundle_context:{intent_id}"
        )

        if bundle_context_raw:
            bundle_context = BundleContext(**bundle_context_raw)
            logger.info(
                "Using enriched bundle context for intent_id=%s",
                intent_id
            )

            resolved_category = bundle_context.resolved_category

            # Use enriched retrieval
            retrieved_products = (
                product_retriever.retrieve(
                    entities=bundle_context.product_query_hints,
                    category=resolved_category or intent_type,
                    constraints=bundle_context.constraints.model_dump(mode="json"),
                    semantic_query=bundle_context.semantic_query,
                )
            )

        else:
            # ── Original Hybrid Retrieval Logic ──
            # Backward-compatible:
            # if shopping_theme is None, BundleGenerator
            # falls back to MOCK_CATALOG

            if shopping_theme:
                try:
                    resolved_category = (
                        category_resolver.resolve(
                            shopping_theme
                        )
                    )

                    retrieved_products = (
                        product_retriever.retrieve(
                            entities=intent_entities,
                            category=resolved_category,
                            constraints=intent_constraints,
                        )
                    )

                except Exception as exc:
                    logger.warning(
                        "Hybrid retrieval failed "
                        "(theme=%s): %s "
                        "— using MOCK_CATALOG",
                        shopping_theme,
                        exc,
                    )

                    retrieved_products = None

    except Exception as exc:
        logger.warning(
            "Clarification bundle context "
            "retrieval failed: %s",
            exc,
        )

        retrieved_products = None

    # Category used for bundle generation/naming:
    # resolved category if retrieved products exist,
    # otherwise original intent_type
    generation_category = (
        resolved_category
        if retrieved_products
        else intent_type
    )
    
    # Step 2: Redis cache check (key includes theme to avoid old/new collision)
    cache_hit = False
    user_id_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
    theme_part = (bundle_context.resolved_category if bundle_context else shopping_theme) or "none"
    cache_key = f"bundle:{generation_category}:{theme_part}:{user_id_hash}"
    
    try:
        cached_data = await cache_get(cache_key)
        if cached_data:
            logger.info(f"Bundle cache hit for key: {cache_key}")
            cache_hit = True
            
            # Reconstruct BundleListResponse from cache
            # (Cache format matches response schema)
            cached_data["cache_hit"] = True
            return BundleListResponse(**cached_data)
    except Exception as exc:
        # Cache errors are non-fatal
        logger.warning(f"Cache lookup failed for key '{cache_key}': {exc}")
    
    # Step 3: Get personalization signals
    try:
        signals = await PersonalizationService.get_signals(user_id, db)
    except Exception as exc:
        logger.error(f"Personalization service failed for user {user_id}: {exc}")
        # Continue with empty signals on error
        from app.services.personalization_service import PersonalizationSignals
        signals = PersonalizationSignals()
    
    # Step 4: Generate 3 bundles (from retrieved products if available, else MOCK_CATALOG)
    try:
        bundles = BundleGenerator.generate(
            generation_category, user_id, signals, products=retrieved_products
        )
    except Exception as exc:
        logger.error(f"Bundle generation failed for intent {intent_type}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Bundle generation failed"
        )
    
    # Step 5: Check inventory for all products
    all_product_ids = [
        item.product_id 
        for bundle in bundles 
        for item in bundle.items
    ]
    
    try:
        inventory_data = await InventoryAdapter.check_batch(all_product_ids)
    except Exception as exc:
        logger.error(f"Inventory check failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Inventory check failed"
        )
    
    # Update bundle items with inventory data
    for bundle in bundles:
        for item in bundle.items:
            inv_info = inventory_data.get(item.product_id, {})
            item.warehouse = inv_info.get("warehouse", "")
    
    # Step 6: Check ETA for all products
    try:
        eta_data = await ETAAdapter.get_batch(all_product_ids)
    except Exception as exc:
        logger.error(f"ETA check failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="ETA check failed"
        )
    
    # Update bundle items with ETA data
    for bundle in bundles:
        for item in bundle.items:
            eta_info = eta_data.get(item.product_id, {})
            item.eta_minutes = eta_info.get("eta_minutes", 60)
            item.eta_label = eta_info.get("eta_label", "In 60 min")
    
    # Step 7: Apply substitutions for OOS items
    try:
        bundles = await SubstitutionEngine.apply(bundles, db)
    except Exception as exc:
        logger.error(f"Substitution engine failed: {exc}")
        # Continue without substitutions on error
        logger.warning("Proceeding without substitutions")
    
    # Step 8: Rank bundles by weighted score
    # Use generation_category so intent-match scoring aligns with bundle.intent_type
    try:
        ranked_bundles = RankingEngine.rank(bundles, generation_category, signals)
    except Exception as exc:
        logger.error(f"Ranking engine failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Bundle ranking failed"
        )
    
    # Step 9: Persist bundles to DB
    try:
        for bundle in ranked_bundles:
            bundle_model = Bundle_Model(
                user_id=user_id,
                intent_id=intent_id,
                name=bundle.bundle_name
            )
            db.add(bundle_model)
            await db.flush()  # Get bundle_model.id
            
            # Add bundle items
            for item in bundle.items:
                bundle_item = BundleItem(
                    bundle_id=bundle_model.id,
                    product_id=item.product_id,
                    product_name=item.name,
                    quantity=item.quantity,
                    price=item.unit_price
                )
                db.add(bundle_item)
        
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error(f"Bundle persistence failed: {exc}")
        # Non-fatal: bundles still returned even if DB save fails
        logger.warning("Bundles not persisted to DB, continuing")
    
    # Step 10: Cache result in Redis
    response_data = BundleListResponse(
        intent_id=str(intent_id),
        recommended=ranked_bundles[0],  # Highest scored
        options=ranked_bundles,
        cache_hit=False
    )
    
    try:
        # Cache as dict (Pydantic model.dict())
        cache_value = response_data.model_dump(mode='json')
        await cache_set(cache_key, cache_value, settings.BUNDLE_CACHE_TTL_SECONDS)
        logger.info(f"Cached bundles with key: {cache_key}")
    except Exception as exc:
        # Cache errors are non-fatal
        logger.warning(f"Cache write failed for key '{cache_key}': {exc}")
    
    # Step 11: Emit bundle.generated event
    try:
        await emit("bundle.generated", {
            "intent_id": str(intent_id),
            "user_id": user_id,
            "intent_type": intent_type,
            "bundle_count": len(ranked_bundles),
            "cache_hit": False
        })
    except Exception as exc:
        # Event emission errors are non-fatal
        logger.warning(f"Event emission failed: {exc}")
    
    # Step 12: Return response
    return response_data
