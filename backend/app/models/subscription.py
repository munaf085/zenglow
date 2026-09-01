"""
SubscriptionPlan and Subscription models.
"""
import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class PlanTier(str, enum.Enum):
    FREE = "FREE"
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class BillingCycle(str, enum.Enum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    TRIAL = "TRIAL"
    PAST_DUE = "PAST_DUE"


class SubscriptionPlan(BaseModel):
    __tablename__ = "subscription_plans"

    tier: Mapped[PlanTier] = mapped_column(Enum(PlanTier), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing is NOT hardcoded — stored in DB so platform admin can change it
    monthly_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    yearly_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    # Feature limits
    max_branches: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_staff: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_services: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    max_bookings_per_month: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    businesses: Mapped[List["Business"]] = relationship(  # type: ignore[name-defined]
        back_populates="subscription_plan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="plan")


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False
    )
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        Enum(BillingCycle), default=BillingCycle.MONTHLY, nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    plan: Mapped["SubscriptionPlan"] = relationship(back_populates="subscriptions")
