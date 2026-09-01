"""
POS & Order Checkout Pydantic Schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class POSCartItem(BaseModel):
    item_type: str = Field(..., pattern="^(SERVICE|PRODUCT|MEMBERSHIP|PACKAGE|GIFT_CARD)$")
    item_id: Optional[UUID] = None
    name: str
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(..., ge=0)
    tax_rate: float = Field(default=18.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)


class POSPaymentTender(BaseModel):
    payment_method: str = Field(..., pattern="^(CASH|CARD|UPI|GIFT_CARD|MEMBERSHIP|OTHER)$")
    amount: float = Field(..., gt=0)
    reference_code: Optional[str] = None


class POSCheckoutRequest(BaseModel):
    branch_id: UUID
    customer_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    items: List[POSCartItem] = Field(..., min_length=1)
    payments: List[POSPaymentTender] = Field(..., min_length=1)
    discount_amount: float = Field(default=0.0, ge=0)
    tip_amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: UUID
    item_type: str
    item_id: Optional[UUID] = None
    name: str
    quantity: int
    unit_price: float
    tax_rate: float
    discount_amount: float
    total_price: float

    class Config:
        from_attributes = True


class OrderPaymentResponse(BaseModel):
    id: UUID
    payment_method: str
    amount: float
    reference_code: Optional[str] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    business_id: UUID
    branch_id: UUID
    customer_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    order_number: str
    status: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    tip_amount: float
    total_amount: float
    notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    payments: List[OrderPaymentResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
