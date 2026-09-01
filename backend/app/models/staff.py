"""
Staff, StaffService, WorkingHours, StaffLeave models.
"""
import enum
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class WeekDay(int, enum.Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class StaffStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"


class Staff(BaseModel, SoftDeleteMixin):
    __tablename__ = "staff"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StaffStatus] = mapped_column(
        Enum(StaffStatus), default=StaffStatus.ACTIVE, nullable=False, index=True
    )
    # Whether customers can book this staff directly
    bookable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    branch: Mapped[Optional["Branch"]] = relationship(back_populates="staff")  # type: ignore[name-defined]
    staff_services: Mapped[List["StaffService"]] = relationship(back_populates="staff")
    working_hours: Mapped[List["WorkingHours"]] = relationship(
        "WorkingHours",
        primaryjoin="and_(WorkingHours.entity_type=='staff', foreign(WorkingHours.entity_id)==Staff.id)",
        viewonly=True,
    )
    leaves: Mapped[List["StaffLeave"]] = relationship(back_populates="staff")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class StaffService(BaseModel):
    __tablename__ = "staff_services"

    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Staff can override service duration
    duration_override_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Staff can override service price
    price_override: Mapped[Optional[float]] = mapped_column(nullable=True)

    staff: Mapped["Staff"] = relationship(back_populates="staff_services")
    service: Mapped["Service"] = relationship(back_populates="staff_services")  # type: ignore[name-defined]


class WorkingHours(BaseModel):
    """
    Stores working hours for either a branch or a staff member.
    entity_type: 'branch' | 'staff'
    entity_id: UUID of the branch or staff
    """
    __tablename__ = "working_hours"

    entity_type: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 0=Monday ... 6=Sunday
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    open_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)   # "09:00"
    close_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "18:00"
    break_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    break_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)


class LeaveType(str, enum.Enum):
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    PERSONAL = "PERSONAL"
    BLOCKED = "BLOCKED"


class StaffLeave(BaseModel):
    __tablename__ = "staff_leaves"

    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType), default=LeaveType.ANNUAL, nullable=False
    )
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)  # ISO date
    end_date: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    staff: Mapped["Staff"] = relationship(back_populates="leaves")
