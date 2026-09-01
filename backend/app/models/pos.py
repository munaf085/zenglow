"""
POS & Order Models:
- Order (POS sale / transaction containing services, products, memberships, packages)
- OrderItem (line item in an order)
- OrderPayment (tender line in split payment, e.g. 500 Cash + 500 Card)
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class OrderStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class OrderItemType(str, Enum):
    SERVICE = "SERVICE"
    PRODUCT = "PRODUCT"
    MEMBERSHIP = "MEMBERSHIP"
    PACKAGE = "PACKAGE"
    GIFT_CARD = "GIFT_CARD"


class PaymentTenderType(str, Enum):
    CASH = "CASH"
    CARD = "CARD"
    UPI = "UPI"
    GIFT_CARD = "GIFT_CARD"
    MEMBERSHIP = "MEMBERSHIP"
    OTHER = "OTHER"


class Order(SoftDeleteMixin, BaseModel):
    """POS Checkout Sale / Order."""
    __tablename__ = "orders"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        String(50), default=OrderStatus.COMPLETED, nullable=False
    )

    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    tip_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )
    payments: Mapped[List["OrderPayment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )
    customer: Mapped[Optional["Customer"]] = relationship(lazy="selectin")  # type: ignore[name-defined]
    staff: Mapped[Optional["Staff"]] = relationship(lazy="selectin")  # type: ignore[name-defined]


class OrderItem(SoftDeleteMixin, BaseModel):
    """Line item in a POS Order."""
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[OrderItemType] = mapped_column(
        String(50), default=OrderItemType.SERVICE, nullable=False
    )
    item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items", lazy="selectin")


class OrderPayment(SoftDeleteMixin, BaseModel):
    """Payment tender line for multi-tender split checkout."""
    __tablename__ = "order_payments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_method: Mapped[PaymentTenderType] = mapped_column(
        String(50), default=PaymentTenderType.CASH, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reference_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g. card last4, upi ref, gift card code

    order: Mapped["Order"] = relationship(back_populates="payments", lazy="selectin")
