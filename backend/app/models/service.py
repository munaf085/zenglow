"""
Service and ServiceCategory models.
"""
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class ServiceCategory(BaseModel, SoftDeleteMixin):
    __tablename__ = "service_categories"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    services: Mapped[List["Service"]] = relationship(back_populates="category")


class Service(BaseModel, SoftDeleteMixin):
    __tablename__ = "services"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("service_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)

    # Timing (in minutes)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    buffer_before_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    buffer_after_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Availability
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    online_booking_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Display
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped[Optional["ServiceCategory"]] = relationship(back_populates="services")
    staff_services: Mapped[List["StaffService"]] = relationship(  # type: ignore[name-defined]
        "StaffService", back_populates="service"
    )
    appointment_items: Mapped[List["AppointmentItem"]] = relationship(  # type: ignore[name-defined]
        "AppointmentItem", back_populates="service"
    )
