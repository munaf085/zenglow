"""
Inventory Pydantic Schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryResponse(ProductCategoryBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    category_id: Optional[UUID] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    cost_price: float = Field(default=0.0, ge=0)
    retail_price: float = Field(..., gt=0)
    tax_rate: float = Field(default=18.0, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[UUID] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    cost_price: Optional[float] = None
    retail_price: Optional[float] = None
    tax_rate: Optional[float] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID
    business_id: UUID
    created_at: datetime
    updated_at: datetime
    is_low_stock: Optional[bool] = False

    class Config:
        from_attributes = True


class StockMovementCreate(BaseModel):
    product_id: UUID
    movement_type: str = Field(..., pattern="^(IN|OUT|SALE|ADJUSTMENT|RETURN)$")
    quantity: int = Field(..., description="Quantity to adjust (positive or negative)")
    unit_cost: Optional[float] = None
    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: UUID
    business_id: UUID
    product_id: UUID
    movement_type: str
    quantity: int
    unit_cost: Optional[float] = None
    reference_order_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
