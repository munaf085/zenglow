"""
Staff and WorkingHours schemas.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.staff import LeaveType, StaffStatus


class WorkingHoursEntry(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    is_open: bool = True
    open_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    close_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    break_start: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    break_end: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")


class WorkingHoursResponse(WorkingHoursEntry):
    id: UUID
    entity_type: str
    entity_id: UUID
    business_id: UUID

    model_config = {"from_attributes": True}


class WorkingHoursSetRequest(BaseModel):
    hours: List[WorkingHoursEntry]


class StaffBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    title: Optional[str] = None
    bio: Optional[str] = None
    bookable: bool = True
    sort_order: int = 0


class StaffCreate(StaffBase):
    branch_id: Optional[UUID] = None
    service_ids: List[UUID] = []


class StaffUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None
    bookable: Optional[bool] = None
    status: Optional[StaffStatus] = None
    branch_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    avatar_url: Optional[str] = None


class StaffResponse(StaffBase):
    id: UUID
    business_id: UUID
    branch_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    status: StaffStatus
    avatar_url: Optional[str] = None
    created_at: datetime
    service_ids: List[UUID] = []

    model_config = {"from_attributes": True}


class StaffLeaveCreate(BaseModel):
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    leave_type: LeaveType = LeaveType.ANNUAL
    reason: Optional[str] = None


class StaffLeaveResponse(StaffLeaveCreate):
    id: UUID
    staff_id: UUID
    approved: bool

    model_config = {"from_attributes": True}
