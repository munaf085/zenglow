"""
Subscription Pydantic Schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.subscription import BillingCycle, PlanTier, SubscriptionStatus


class SubscriptionPlanResponse(BaseModel):
    id: UUID
    tier: PlanTier
    name: str
    description: Optional[str] = None
    monthly_price: float
    yearly_price: float
    currency: str = "INR"
    max_branches: int
    max_staff: int
    max_services: int
    max_bookings_per_month: int
    is_active: bool

    class Config:
        from_attributes = True


class CreateSubscriptionOrderRequest(BaseModel):
    business_id: UUID
    plan_id: UUID
    billing_cycle: BillingCycle = BillingCycle.MONTHLY


class SubscriptionOrderResponse(BaseModel):
    provider_order_id: str
    amount: float
    currency: str
    key_id: str
    business_id: UUID
    plan_id: UUID
    billing_cycle: BillingCycle
    plan_name: str


class VerifySubscriptionRequest(BaseModel):
    business_id: UUID
    plan_id: UUID
    billing_cycle: BillingCycle
    provider_payment_id: str
    provider_order_id: str
    provider_signature: str


class SubscriptionDetailsResponse(BaseModel):
    id: UUID
    business_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    start_date: datetime
    end_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    plan: Optional[SubscriptionPlanResponse] = None

    class Config:
        from_attributes = True
