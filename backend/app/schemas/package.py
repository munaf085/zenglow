"""
Package Pydantic Schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PackageItemInput(BaseModel):
    service_id: UUID
    quantity: int = Field(default=1, ge=1)


class PackageTemplateBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    validity_days: int = Field(default=180, ge=1)
    is_active: bool = True


class PackageTemplateCreate(PackageTemplateBase):
    items: List[PackageItemInput] = Field(..., min_length=1)


class PackageTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    validity_days: Optional[int] = None
    is_active: Optional[bool] = None


class PackageItemTemplateResponse(BaseModel):
    id: UUID
    service_id: UUID
    quantity: int

    class Config:
        from_attributes = True


class PackageTemplateResponse(PackageTemplateBase):
    id: UUID
    business_id: UUID
    items: List[PackageItemTemplateResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerPackageCreate(BaseModel):
    customer_id: UUID
    package_template_id: UUID


class CustomerPackageItemResponse(BaseModel):
    id: UUID
    service_id: UUID
    total_quantity: int
    used_quantity: int
    remaining_quantity: Optional[int] = 0

    class Config:
        from_attributes = True


class CustomerPackageResponse(BaseModel):
    id: UUID
    business_id: UUID
    customer_id: UUID
    package_template_id: UUID
    status: str
    purchase_date: datetime
    expiry_date: datetime
    items: List[CustomerPackageItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class RedeemPackageItemRequest(BaseModel):
    service_id: UUID
    appointment_id: Optional[UUID] = None
