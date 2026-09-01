"""
Booking / Appointment endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.appointment import AppointmentStatus
from app.schemas.booking import (
    AppointmentResponse,
    AvailabilityRequest,
    AvailabilityResponse,
    CancelBookingRequest,
    CreateBookingRequest,
)
from app.schemas.common import MessageResponse
from app.services.availability_service import AvailabilityService
from app.services.booking_service import BookingService

router = APIRouter(tags=["bookings"])


def _booking_svc(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> BookingService:
    return BookingService(db, redis)


def _avail_svc(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> AvailabilityService:
    return AvailabilityService(db, redis)


# ── Availability ──────────────────────────────────────────────────────────────


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    business_id: UUID = Query(...),
    branch_id: UUID = Query(...),
    service_id: UUID = Query(...),
    date: str = Query(..., description="ISO date: YYYY-MM-DD"),
    staff_id: Optional[UUID] = Query(default=None),
    svc: AvailabilityService = Depends(_avail_svc),
):
    """Return available time slots for booking a service."""
    from datetime import date as date_type
    target_date = date_type.fromisoformat(date)
    return await svc.get_availability(
        business_id=business_id,
        branch_id=branch_id,
        service_id=service_id,
        target_date=target_date,
        staff_id=staff_id,
    )


# ── Booking CRUD ──────────────────────────────────────────────────────────────


@router.post("/bookings", response_model=AppointmentResponse, status_code=201)
async def create_booking(
    data: CreateBookingRequest,
    current_user: CurrentUser,
    svc: BookingService = Depends(_booking_svc),
):
    """Create a new appointment booking."""
    return await svc.create_booking(data, current_user)


@router.get("/bookings/me", response_model=List[AppointmentResponse])
async def my_bookings(
    current_user: CurrentUser,
    status: Optional[AppointmentStatus] = Query(default=None),
    svc: BookingService = Depends(_booking_svc),
):
    """Get the current customer's bookings."""
    return await svc.list_customer_appointments(current_user, status)


@router.get("/bookings/{appointment_id}", response_model=AppointmentResponse)
async def get_booking(
    appointment_id: UUID,
    current_user: CurrentUser,
    svc: BookingService = Depends(_booking_svc),
):
    return await svc.get_appointment(appointment_id, current_user)


@router.post("/bookings/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_booking(
    appointment_id: UUID,
    data: CancelBookingRequest,
    current_user: CurrentUser,
    svc: BookingService = Depends(_booking_svc),
):
    return await svc.cancel_booking(appointment_id, current_user, data)


@router.get("/businesses/{business_id}/appointments", response_model=List[AppointmentResponse])
async def list_business_appointments(
    business_id: UUID,
    branch_id: Optional[UUID] = Query(default=None),
    staff_id: Optional[UUID] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    appt_status: Optional[AppointmentStatus] = Query(default=None, alias="status"),
    current_user: CurrentUser = None,
    svc: BookingService = Depends(_booking_svc),
):
    """Business-side: list appointments with filters."""
    return await svc.list_business_appointments(
        business_id=business_id,
        branch_id=branch_id,
        staff_id=staff_id,
        start_date=start_date,
        end_date=end_date,
        status=appt_status,
        user=current_user,
    )


@router.patch(
    "/businesses/{business_id}/appointments/{appointment_id}/status",
    response_model=AppointmentResponse,
)
async def update_appointment_status(
    business_id: UUID,
    appointment_id: UUID,
    new_status: AppointmentStatus = Query(...),
    current_user: CurrentUser = None,
    svc: BookingService = Depends(_booking_svc),
):
    return await svc.update_appointment_status(appointment_id, new_status, current_user)


@router.post(
    "/bookings/{appointment_id}/confirm-deposit",
    response_model=AppointmentResponse,
)
async def confirm_deposit(
    appointment_id: UUID,
    current_user: CurrentUser,
    svc: BookingService = Depends(_booking_svc),
):
    """Customer or staff confirms deposit payment to transition booking from PENDING to CONFIRMED."""
    return await svc.confirm_deposit_payment(appointment_id, current_user)
