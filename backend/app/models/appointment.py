"""
Appointment and AppointmentItem models.
"""
import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"           # Awaiting confirmation / payment
    CONFIRMED = "CONFIRMED"       # Confirmed
    IN_PROGRESS = "IN_PROGRESS"   # Service in progress
    COMPLETED = "COMPLETED"       # Service completed
    CANCELLED = "CANCELLED"       # Cancelled
    NO_SHOW = "NO_SHOW"           # Customer didn't arrive
    RESCHEDULED = "RESCHEDULED"   # Moved to another slot


# Explicit state transition map for appointment lifecycle
APPOINTMENT_TRANSITIONS: dict[AppointmentStatus, list[AppointmentStatus]] = {
    AppointmentStatus.PENDING: [
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    ],
    AppointmentStatus.CONFIRMED: [
        AppointmentStatus.IN_PROGRESS,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
        AppointmentStatus.RESCHEDULED,
    ],
    AppointmentStatus.IN_PROGRESS: [
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
    ],
    AppointmentStatus.COMPLETED: [],  # terminal
    AppointmentStatus.CANCELLED: [],  # terminal
    AppointmentStatus.NO_SHOW: [],  # terminal
    AppointmentStatus.RESCHEDULED: [
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    ],
}


class AppointmentSource(str, enum.Enum):
    """
    Booking source attribution — critical for monetization.

    DIRECT sources: no commission charged.
      ONLINE   — customer booked via business's direct booking link
      WALK_IN  — in-person, no prior online booking
      PHONE    — booked over the phone by receptionist/staff
      STAFF    — created by staff on behalf of customer (dashboard)

    MARKETPLACE sources: commission may be charged when marketplace
    brings a net-new customer to the salon.
      MARKETPLACE — customer discovered and booked via Zenglow marketplace
    """
    # ── Direct (no commission) ────────────────────────────────────────────────
    ONLINE = "ONLINE"        # Direct booking link / business widget
    WALK_IN = "WALK_IN"      # Walk-in, created by staff
    PHONE = "PHONE"          # Phone booking by receptionist
    STAFF = "STAFF"          # Staff-created booking in dashboard

    # ── Marketplace (commission applies) ─────────────────────────────────────
    MARKETPLACE = "MARKETPLACE"  # Discovered via Zenglow marketplace


# Sources that may incur marketplace commission
MARKETPLACE_SOURCES = {AppointmentSource.MARKETPLACE}

# Sources that are 100% direct (no commission)
DIRECT_SOURCES = {
    AppointmentSource.ONLINE,
    AppointmentSource.WALK_IN,
    AppointmentSource.PHONE,
    AppointmentSource.STAFF,
}


def is_marketplace_booking(source: AppointmentSource) -> bool:
    return source in MARKETPLACE_SOURCES


class Appointment(BaseModel, SoftDeleteMixin):
    __tablename__ = "appointments"

    # Tenant key
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
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Appointment timing
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False, index=True
    )
    source: Mapped[AppointmentSource] = mapped_column(
        Enum(AppointmentSource), default=AppointmentSource.ONLINE, nullable=False, index=True
    )

    # ── Marketplace attribution & commission ──────────────────────────────────
    # is_marketplace_booking: True when source == MARKETPLACE
    # Commission is calculated on total_amount at the rate defined in subscription plan
    is_marketplace_booking: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    commission_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True  # e.g. 0.0500 = 5%
    )
    commission_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    commission_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # First-time customer from marketplace? (used for commission eligibility)
    is_new_customer_via_marketplace: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Pricing summary (snapshot at booking time)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    deposit_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    # Notes
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    staff_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Reminder tracking
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_2h_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relations
    branch: Mapped["Branch"] = relationship(back_populates="appointments")  # type: ignore[name-defined]
    customer: Mapped["Customer"] = relationship(back_populates="appointments")  # type: ignore[name-defined]
    items: Mapped[List["AppointmentItem"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan", lazy="selectin"
    )
    payment: Mapped[Optional["Payment"]] = relationship(  # type: ignore[name-defined]
        "Payment", back_populates="appointment", uselist=False
    )
    review: Mapped[Optional["Review"]] = relationship(  # type: ignore[name-defined]
        "Review", back_populates="appointment", uselist=False
    )


class AppointmentItem(BaseModel):
    """One service line within an appointment (an appointment can have multiple services)."""
    __tablename__ = "appointment_items"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Snapshot of service details at booking time
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    appointment: Mapped["Appointment"] = relationship(back_populates="items")
    service: Mapped["Service"] = relationship(back_populates="appointment_items")  # type: ignore[name-defined]
