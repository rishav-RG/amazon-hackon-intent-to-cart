from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.user import get_current_user_id
from app.utils.cache import cache_get, cache_set
from app.models.cart import Cart_Model, CartItem
from app.adapters.catalog_adapter import ProductCatalogAdapter
from app.schemas.checkout import BuyAgainItem

router = APIRouter(prefix="/v1", tags=["buy-again"])

BUY_AGAIN_TTL = 3600  # 1 hour


@router.get("/buy-again", response_model=list[BuyAgainItem])
async def buy_again(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"buy_again:{user_id}"

    # Cache-first
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    # DB fallback: Cart join CartItem for checked-out carts
    result = await db.execute(
        select(CartItem)
        .join(Cart_Model, CartItem.cart_id == Cart_Model.id)
        .where(Cart_Model.user_id == user_id, Cart_Model.status == "checked_out")
    )
    items = result.scalars().all()

    if not items:
        return []

    # Enrich via ProductCatalogAdapter
    product_ids = list({item.product_id for item in items})
    catalog_data = await ProductCatalogAdapter.get_products(product_ids)

    buy_again_items = [
        {
            "productId": pid,
            "productName": catalog_data.get(pid, {}).get("name", "Unknown"),
            "lastOrderedAt": catalog_data.get(pid, {}).get("lastOrderedAt", ""),
        }
        for pid in product_ids
    ]

    # Populate cache before returning
    await cache_set(cache_key, buy_again_items, BUY_AGAIN_TTL)

    return buy_again_items
