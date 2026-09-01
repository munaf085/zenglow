"""
Customer model — linked to User, but with business-specific CRM data.
"""
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class Customer(BaseModel, SoftDeleteMixin):
    __tablename__ = "customers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # CRM data (not tied to a specific business — global customer profile)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # comma-separated
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_opt_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="customer_profile")  # type: ignore[name-defined]
    appointments: Mapped[List["Appointment"]] = relationship(  # type: ignore[name-defined]
        "Appointment", back_populates="customer"
    )
    reviews: Mapped[List["Review"]] = relationship(  # type: ignore[name-defined]
        "Review", back_populates="customer"
    )
    favourite_businesses: Mapped[List["FavouriteBusiness"]] = relationship(
        back_populates="customer"
    )


class FavouriteBusiness(BaseModel):
    __tablename__ = "favourite_businesses"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer: Mapped["Customer"] = relationship(back_populates="favourite_businesses")
