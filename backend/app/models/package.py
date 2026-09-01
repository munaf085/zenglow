"""
Package Models:
- PackageTemplate (bundled services created by salon, e.g. "Hair Spa + Facial Combo")
- PackageItemTemplate (service & count inside a package template)
- CustomerPackage (purchased package by customer)
- CustomerPackageItem (usage tracking per service in package, e.g. 2/3 used)
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class PackageStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXHAUSTED = "EXHAUSTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PackageTemplate(SoftDeleteMixin, BaseModel):
    """Bundled service package created by the salon."""
    __tablename__ = "package_templates"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    validity_days: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    items: Mapped[List["PackageItemTemplate"]] = relationship(
        back_populates="package_template", cascade="all, delete-orphan", lazy="selectin"
    )
    customer_packages: Mapped[List["CustomerPackage"]] = relationship(
        back_populates="package_template", cascade="all, delete-orphan", lazy="selectin"
    )


class PackageItemTemplate(SoftDeleteMixin, BaseModel):
    """Specific service included in a package template with quantity."""
    __tablename__ = "package_item_templates"

    package_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("package_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    package_template: Mapped["PackageTemplate"] = relationship(back_populates="items", lazy="selectin")
    service: Mapped["Service"] = relationship(lazy="selectin")  # type: ignore[name-defined]


class CustomerPackage(SoftDeleteMixin, BaseModel):
    """Package purchased by customer."""
    __tablename__ = "customer_packages"

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
    package_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("package_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[PackageStatus] = mapped_column(
        String(50), default=PackageStatus.ACTIVE, nullable=False
    )
    purchase_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    package_template: Mapped["PackageTemplate"] = relationship(back_populates="customer_packages", lazy="selectin")
    customer: Mapped["Customer"] = relationship(lazy="selectin")  # type: ignore[name-defined]
    items: Mapped[List["CustomerPackageItem"]] = relationship(
        back_populates="customer_package", cascade="all, delete-orphan", lazy="selectin"
    )


class CustomerPackageItem(SoftDeleteMixin, BaseModel):
    """Usage tracker for each service in a customer's package."""
    __tablename__ = "customer_package_items"

    customer_package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
    )
    total_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    used_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    customer_package: Mapped["CustomerPackage"] = relationship(back_populates="items", lazy="selectin")
    service: Mapped["Service"] = relationship(lazy="selectin")  # type: ignore[name-defined]
