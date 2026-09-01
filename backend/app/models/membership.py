"""
Membership Models:
- MembershipPlan (tiers created by salon, e.g. Gold/VIP)
- CustomerMembership (active/past subscriptions for customers)
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class MembershipPlan(SoftDeleteMixin, BaseModel):
    """Salon membership tier (e.g. VIP Club ₹1,999 / year)."""
    __tablename__ = "membership_plans"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)  # 1, 3, 6, 12 months

    # Benefits
    discount_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=10.0, nullable=False)
    free_services_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    customer_memberships: Mapped[List["CustomerMembership"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", lazy="selectin"
    )


class CustomerMembership(SoftDeleteMixin, BaseModel):
    """Active customer membership subscription."""
    __tablename__ = "customer_memberships"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("membership_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[MembershipStatus] = mapped_column(
        String(50), default=MembershipStatus.ACTIVE, nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    free_services_remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plan: Mapped["MembershipPlan"] = relationship(back_populates="customer_memberships", lazy="selectin")
    customer: Mapped["Customer"] = relationship(lazy="selectin")  # type: ignore[name-defined]
