"""
Business and Branch models — core tenant entities.
"""
import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class BusinessStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class VerificationStatus(str, enum.Enum):
    """
    Explicit state machine for business verification.
    Transitions:
        NOT_APPLIED → APPLIED (owner submits docs)
        APPLIED → UNDER_REVIEW (admin picks up)
        UNDER_REVIEW → APPROVED (admin approves)
        UNDER_REVIEW → REJECTED (admin rejects with reason)
        REJECTED → APPLIED (owner reapplies)
    """
    NOT_APPLIED = "NOT_APPLIED"
    APPLIED = "APPLIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# Valid state transitions — enforced in service layer
VERIFICATION_TRANSITIONS: dict[str, list[str]] = {
    VerificationStatus.NOT_APPLIED: [VerificationStatus.APPLIED],
    VerificationStatus.APPLIED:     [VerificationStatus.UNDER_REVIEW, VerificationStatus.REJECTED],
    VerificationStatus.UNDER_REVIEW:[VerificationStatus.APPROVED, VerificationStatus.REJECTED],
    VerificationStatus.APPROVED:    [],  # terminal — admin can suspend instead
    VerificationStatus.REJECTED:    [VerificationStatus.APPLIED],  # owner can reapply
}


class BusinessCategory(str, enum.Enum):
    SALON = "SALON"
    SPA = "SPA"
    BARBER = "BARBER"
    BEAUTY = "BEAUTY"
    WELLNESS = "WELLNESS"
    NAIL_STUDIO = "NAIL_STUDIO"
    MASSAGE = "MASSAGE"
    OTHER = "OTHER"


class Business(BaseModel, SoftDeleteMixin):
    __tablename__ = "businesses"

    # Tenant identifier
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[BusinessCategory] = mapped_column(
        Enum(BusinessCategory), nullable=False, default=BusinessCategory.SALON
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[BusinessStatus] = mapped_column(
        Enum(BusinessStatus), default=BusinessStatus.PENDING, nullable=False, index=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Verification state machine ────────────────────────────────────────────
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        default=VerificationStatus.NOT_APPLIED,
        nullable=False,
        index=True,
    )
    verification_submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    verification_rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Booking configuration
    booking_advance_days: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    cancellation_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    cancellation_policy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deposit_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deposit_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    # Subscription
    subscription_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True
    )

    branches: Mapped[List["Branch"]] = relationship(back_populates="business", lazy="selectin")
    subscription_plan: Mapped[Optional["SubscriptionPlan"]] = relationship(  # type: ignore[name-defined]
        back_populates="businesses"
    )


class Branch(BaseModel, SoftDeleteMixin):
    __tablename__ = "branches"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Booking config overrides
    booking_advance_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cancellation_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    business: Mapped["Business"] = relationship(back_populates="branches")
    working_hours: Mapped[List["WorkingHours"]] = relationship(  # type: ignore[name-defined]
        "WorkingHours",
        primaryjoin="and_(WorkingHours.entity_type=='branch', foreign(WorkingHours.entity_id)==Branch.id)",
        viewonly=True,
    )
    staff: Mapped[List["Staff"]] = relationship(  # type: ignore[name-defined]
        "Staff", back_populates="branch"
    )
    appointments: Mapped[List["Appointment"]] = relationship(  # type: ignore[name-defined]
        "Appointment", back_populates="branch"
    )
