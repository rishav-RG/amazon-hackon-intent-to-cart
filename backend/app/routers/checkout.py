from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.user import get_current_user_id
from app.services.checkout_service import (
    CheckoutService,
    CartNotActiveError,
    CartEmptyError,
    ItemsOutOfStockError,
)
from app.schemas.checkout import CheckoutRequest, CheckoutResponse

router = APIRouter(prefix="/v1", tags=["checkout"])


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CheckoutService(db)
    try:
        result = await service.execute(body.cartId, user_id)
        return result
    except CartNotActiveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CartEmptyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ItemsOutOfStockError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ITEMS_OUT_OF_STOCK",
                "items": e.oos_items,
            },
        )
