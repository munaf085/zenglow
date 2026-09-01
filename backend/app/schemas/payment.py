"""
Payment schemas.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.payment import PaymentProvider, PaymentStatus


class CreatePaymentOrderRequest(BaseModel):
    appointment_id: UUID
    amount: float = Field(gt=0)
    currency: str = "INR"


class PaymentOrderResponse(BaseModel):
    payment_id: UUID
    provider_order_id: str
    amount: float
    currency: str
    provider: PaymentProvider
    status: PaymentStatus
    provider_key: Optional[str] = None  # public key for frontend SDK


class VerifyPaymentRequest(BaseModel):
    payment_id: UUID
    provider_order_id: str
    provider_payment_id: str
    provider_signature: str


class PaymentResponse(BaseModel):
    id: UUID
    business_id: UUID
    appointment_id: Optional[UUID] = None
    customer_id: UUID
    amount: float
    currency: str
    provider: PaymentProvider
    status: PaymentStatus
    provider_order_id: Optional[str] = None
    provider_payment_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundRequest(BaseModel):
    amount: float = Field(gt=0)
    reason: Optional[str] = None


class RefundResponse(BaseModel):
    id: UUID
    payment_id: UUID
    amount: float
    status: str
    provider_refund_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
