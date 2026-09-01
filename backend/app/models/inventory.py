"""
Inventory & Product Models:
- ProductCategory
- Product
- StockMovement
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class StockMovementType(str, Enum):
    IN = "IN"                  # Restock / purchase from supplier
    OUT = "OUT"                # Write-off / damage / internal salon use
    SALE = "SALE"              # Sold via POS
    ADJUSTMENT = "ADJUSTMENT"  # Inventory count correction
    RETURN = "RETURN"          # Customer returned item


class ProductCategory(SoftDeleteMixin, BaseModel):
    __tablename__ = "product_categories"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    products: Mapped[List["Product"]] = relationship(
        back_populates="category", cascade="all, delete-orphan", lazy="selectin"
    )


class Product(SoftDeleteMixin, BaseModel):
    __tablename__ = "products"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    cost_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    retail_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.0, nullable=False)

    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped[Optional["ProductCategory"]] = relationship(
        back_populates="products", lazy="selectin"
    )
    movements: Mapped[List["StockMovement"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )


class StockMovement(SoftDeleteMixin, BaseModel):
    __tablename__ = "stock_movements"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movement_type: Mapped[StockMovementType] = mapped_column(
        String(50), default=StockMovementType.IN, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # positive for IN/RETURN, negative or positive handled
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    reference_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    product: Mapped["Product"] = relationship(back_populates="movements", lazy="selectin")
