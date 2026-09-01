"""
Membership Pydantic Schemas.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MembershipPlanBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    duration_months: int = Field(default=12, ge=1, le=60)
    discount_percentage: float = Field(default=10.0, ge=0, le=100)
    free_services_count: int = Field(default=0, ge=0)
    is_active: bool = True


class MembershipPlanCreate(MembershipPlanBase):
    pass


class MembershipPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_months: Optional[int] = None
    discount_percentage: Optional[float] = None
    free_services_count: Optional[int] = None
    is_active: Optional[bool] = None


class MembershipPlanResponse(MembershipPlanBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerMembershipCreate(BaseModel):
    customer_id: UUID
    plan_id: UUID
    notes: Optional[str] = None


class CustomerMembershipResponse(BaseModel):
    id: UUID
    business_id: UUID
    customer_id: UUID
    plan_id: UUID
    status: str
    start_date: datetime
    end_date: datetime
    free_services_remaining: int
    notes: Optional[str] = None
    plan: Optional[MembershipPlanResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True
