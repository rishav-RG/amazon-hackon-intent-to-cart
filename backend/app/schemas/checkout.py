from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    cartId: str


class CheckoutItemResponse(BaseModel):
    productId: str
    quantity: int
    price: float


class CheckoutResponse(BaseModel):
    orderId: str
    status: str  # "confirmed"
    items: list[CheckoutItemResponse]
    total: float


class OOSErrorDetail(BaseModel):
    productId: str
    availableQuantity: int
    substitutes: list[str]


class BuyAgainItem(BaseModel):
    productId: str
    productName: str
    lastOrderedAt: str
