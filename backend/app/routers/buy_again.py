from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.user import get_current_user_id
from app.utils.cache import cache_get, cache_set
from app.models.cart import Cart_Model, CartItem
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
        select(CartItem, Cart_Model.created_at)
        .join(Cart_Model, CartItem.cart_id == Cart_Model.id)
        .where(Cart_Model.user_id == user_id, Cart_Model.status == "checked_out")
    )
    rows = result.all()

    if not rows:
        return []

    # Deduplicate by product_id, keep latest order timestamp
    seen: dict[str, dict] = {}
    for item, cart_created_at in rows:
        pid = item.product_id
        if pid not in seen:
            seen[pid] = {
                "productId": pid,
                "productName": item.product_name or f"Product {pid}",
                "lastOrderedAt": str(cart_created_at) if cart_created_at else "",
            }

    buy_again_items = list(seen.values())

    # Populate cache before returning
    await cache_set(cache_key, buy_again_items, BUY_AGAIN_TTL)

    return buy_again_items
