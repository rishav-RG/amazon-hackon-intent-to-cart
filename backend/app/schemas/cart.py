from __future__ import annotations
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class AddOperation(BaseModel):
    type: Literal["add"]
    productId: str
    quantity: int = Field(..., gt=0)


class RemoveOperation(BaseModel):
    type: Literal["remove"]
    productId: str


class UpdateOperation(BaseModel):
    type: Literal["update"]
    productId: str
    quantity: int = Field(..., gt=0)


CartOperation = Annotated[
    Union[AddOperation, RemoveOperation, UpdateOperation],
    Field(discriminator="type"),
]


class CartPatchRequest(BaseModel):
    operations: list[CartOperation]
    version: Optional[int] = Field(default=None, ge=0)


class CartItemResponse(BaseModel):
    productId: str
    productName: str = ""
    quantity: int
    price: float = 0.0
    isSubstituted: bool = False


class CartResponse(BaseModel):
    cartId: str
    version: int
    items: list[CartItemResponse]
    total: float
    status: str
