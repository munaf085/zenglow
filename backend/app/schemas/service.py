"""
Service and ServiceCategory schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ServiceCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    sort_order: int = 0


class ServiceCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceCategoryResponse(ServiceCategoryCreate):
    id: UUID
    business_id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)
    duration_minutes: int = Field(ge=5, le=480)
    buffer_before_minutes: int = Field(default=0, ge=0)
    buffer_after_minutes: int = Field(default=0, ge=0)
    is_active: bool = True
    online_booking_enabled: bool = True
    sort_order: int = 0


class ServiceCreate(ServiceBase):
    category_id: Optional[UUID] = None
    staff_ids: List[UUID] = []


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    tax_rate: Optional[float] = Field(default=None, ge=0, le=100)
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=480)
    buffer_before_minutes: Optional[int] = None
    buffer_after_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    online_booking_enabled: Optional[bool] = None
    category_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    image_url: Optional[str] = None


class ServiceResponse(ServiceBase):
    id: UUID
    business_id: UUID
    category_id: Optional[UUID] = None
    image_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
