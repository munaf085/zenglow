"""
Admin schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.business import BusinessStatus
from app.models.payment import PaymentStatus
from app.models.subscription import PlanTier


class AdminBusinessUpdate(BaseModel):
    status: Optional[BusinessStatus] = None
    is_verified: Optional[bool] = None
    is_featured: Optional[bool] = None


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class DashboardStats(BaseModel):
    total_businesses: int
    active_businesses: int
    total_users: int
    total_bookings: int
    total_revenue: float
    bookings_today: int
    new_businesses_this_month: int
    new_users_this_month: int


class RevenueReport(BaseModel):
    period: str
    total_revenue: float
    total_bookings: int
    average_booking_value: float


class SubscriptionPlanCreate(BaseModel):
    tier: PlanTier
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    monthly_price: float = Field(ge=0)
    yearly_price: float = Field(ge=0)
    currency: str = "INR"
    max_branches: int = Field(default=1, ge=1)
    max_staff: int = Field(default=5, ge=1)
    max_services: int = Field(default=20, ge=1)
    max_bookings_per_month: int = Field(default=100, ge=1)


class SubscriptionPlanResponse(SubscriptionPlanCreate):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
