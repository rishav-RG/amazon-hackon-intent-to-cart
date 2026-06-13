from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.user import get_current_user_id
from app.services.cart_service import CartService
from app.schemas.cart import CartPatchRequest, CartResponse

router = APIRouter(prefix="/v1", tags=["cart"])


@router.patch("/cart", response_model=CartResponse)
async def patch_cart(
    body: CartPatchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart = await service.get_by_user(user_id)
    if cart is None:
        cart = await service.create(user_id)

    # Optimistic lock check
    if not service.check_version(cart, body.version):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Version conflict",
                "serverVersion": cart.version,
                "cart": service._serialize(cart),
            },
        )

    # Apply operations
    operations = [op.model_dump() for op in body.operations]
    cart = await service.apply_operations(cart, operations)
    cart = await service.save(cart)

    return service._serialize(cart)


@router.get("/cart/{cart_id}", response_model=CartResponse)
async def get_cart(
    cart_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    cart_data = await service.get(cart_id)
    if cart_data is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart_data
