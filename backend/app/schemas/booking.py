"""
Booking-related schemas.
"""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentSource, AppointmentStatus


class AvailabilityRequest(BaseModel):
    business_id: UUID
    branch_id: UUID
    service_id: UUID
    date: date
    staff_id: Optional[UUID] = None  # None = any available staff


class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    staff_id: UUID
    staff_name: str
    available: bool = True


class AvailabilityResponse(BaseModel):
    date: date
    service_id: UUID
    service_name: str
    duration_minutes: int
    slots: List[TimeSlot]


class BookingItemRequest(BaseModel):
    service_id: UUID
    staff_id: Optional[UUID] = None  # None = any available
    start_time: datetime


class CreateBookingRequest(BaseModel):
    business_id: UUID
    branch_id: UUID
    items: List[BookingItemRequest] = Field(min_length=1)
    customer_notes: Optional[str] = None
    source: str = "ONLINE"  # ONLINE | MARKETPLACE | WALK_IN | PHONE | STAFF


class AppointmentItemResponse(BaseModel):
    id: UUID
    service_id: UUID
    service_name: str
    staff_id: UUID
    duration_minutes: int
    price: float
    tax_rate: float
    start_time: datetime
    end_time: datetime

    model_config = {"from_attributes": True}


class AppointmentResponse(BaseModel):
    id: UUID
    business_id: UUID
    branch_id: UUID
    customer_id: UUID
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    source: AppointmentSource
    subtotal: float
    tax_amount: float
    total_amount: float
    deposit_amount: float
    customer_notes: Optional[str] = None
    items: List[AppointmentItemResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class AppointmentUpdateRequest(BaseModel):
    status: Optional[AppointmentStatus] = None
    staff_notes: Optional[str] = None
    customer_notes: Optional[str] = None


class CancelBookingRequest(BaseModel):
    reason: Optional[str] = None


class RescheduleRequest(BaseModel):
    new_start_time: datetime
    staff_id: Optional[UUID] = None
