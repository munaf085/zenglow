"""
Business and Branch Pydantic schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from app.models.business import BusinessCategory, BusinessStatus


class BranchBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    is_primary: bool = False
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class BranchResponse(BranchBase):
    id: UUID
    business_id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BusinessBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: BusinessCategory = BusinessCategory.SALON
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    website: Optional[str] = None
    booking_advance_days: int = Field(default=60, ge=1, le=365)
    cancellation_hours: int = Field(default=24, ge=0)
    cancellation_policy: Optional[str] = None
    deposit_required: bool = False
    deposit_percentage: Optional[float] = Field(default=None, ge=0, le=100)


class BusinessCreate(BusinessBase):
    branch: Optional[BranchCreate] = None  # optionally create the primary branch inline


class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[BusinessCategory] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    instagram_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
    tiktok_url: Optional[HttpUrl] = None

    booking_advance_days: Optional[int] = Field(default=None, ge=1, le=365)
    cancellation_hours: Optional[int] = Field(default=None, ge=0)
    cancellation_policy: Optional[str] = None
    deposit_required: Optional[bool] = None
    deposit_percentage: Optional[float] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None


class BusinessResponse(BusinessBase):
    id: UUID
    slug: str
    owner_id: UUID
    status: BusinessStatus
    is_verified: bool
    is_featured: bool

    instagram_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
    tiktok_url: Optional[HttpUrl] = None

    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    created_at: datetime
    branches: List[BranchResponse] = []

    model_config = {"from_attributes": True}


class BusinessListResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    category: BusinessCategory
    description: Optional[str] = None
    logo_url: Optional[str] = None
    status: BusinessStatus
    is_verified: bool
    is_featured: bool
    city: Optional[str] = None  # from primary branch
    created_at: datetime

    model_config = {"from_attributes": True}