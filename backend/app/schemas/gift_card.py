"""
Gift Card Pydantic Schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GiftCardCreate(BaseModel):
    amount: float = Field(..., gt=0)
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    message: Optional[str] = None
    purchaser_customer_id: Optional[UUID] = None
    expiry_days: Optional[int] = Field(default=365, ge=1)


class GiftCardTransactionResponse(BaseModel):
    id: UUID
    transaction_type: str
    amount: float
    balance_after: float
    reference_order_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GiftCardResponse(BaseModel):
    id: UUID
    business_id: UUID
    code: str
    initial_balance: float
    current_balance: float
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    message: Optional[str] = None
    expiry_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GiftCardBalanceCheckResponse(BaseModel):
    valid: bool
    code: str
    current_balance: float
    expiry_date: Optional[datetime] = None
    recipient_name: Optional[str] = None


class GiftCardRedeemRequest(BaseModel):
    code: str
    amount: float = Field(..., gt=0)
    reference_order_id: Optional[UUID] = None
