"""
AvailabilityService — the heart of the booking engine.

Calculates available time slots taking into account:
  - Business opening hours
  - Branch opening hours
  - Staff working hours
  - Staff leaves
  - Staff breaks
  - Existing confirmed/pending appointments
  - Service duration + buffer time
"""
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, SlotUnavailableError
from app.core.logging import get_logger
from app.models.appointment import Appointment, AppointmentItem, AppointmentStatus
from app.models.service import Service
from app.models.staff import Staff, StaffLeave, StaffService as StaffServiceModel, WorkingHours
from app.schemas.booking import AvailabilityResponse, TimeSlot

logger = get_logger(__name__)

SLOT_INTERVAL_MINUTES = 15  # granularity of slot grid


class AvailabilityService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis

    async def get_availability(
        self,
        business_id: UUID,
        branch_id: UUID,
        service_id: UUID,
        target_date: date,
        staff_id: Optional[UUID] = None,
    ) -> AvailabilityResponse:
        """Return all available time slots for a service on a given date."""

        # 1. Load service
        service = await self._get_service(business_id, service_id)
        if not service.online_booking_enabled:
            raise SlotUnavailableError("This service does not accept online bookings")

        total_duration = (
            service.buffer_before_minutes
            + service.duration_minutes
            + service.buffer_after_minutes
        )

        # 2. Find eligible staff
        eligible_staff = await self._get_eligible_staff(business_id, branch_id, service_id, staff_id)
        if not eligible_staff:
            return AvailabilityResponse(
                date=target_date,
                service_id=service_id,
                service_name=service.name,
                duration_minutes=service.duration_minutes,
                slots=[],
            )

        # 3. For each staff member, compute available windows
        slots: List[TimeSlot] = []
        for staff in eligible_staff:
            staff_slots = await self._get_staff_slots(
                staff=staff,
                business_id=business_id,
                branch_id=branch_id,
                target_date=target_date,
                service_duration=service.duration_minutes,
                buffer_before=service.buffer_before_minutes,
                buffer_after=service.buffer_after_minutes,
            )
            for slot_start in staff_slots:
                slot_end = slot_start + timedelta(minutes=service.duration_minutes)
                slots.append(
                    TimeSlot(
                        start_time=slot_start,
                        end_time=slot_end,
                        staff_id=staff.id,
                        staff_name=staff.full_name,
                        available=True,
                    )
                )

        # De-duplicate by time+staff and sort
        slots.sort(key=lambda s: (s.start_time, s.staff_name))

        return AvailabilityResponse(
            date=target_date,
            service_id=service_id,
            service_name=service.name,
            duration_minutes=service.duration_minutes,
            slots=slots,
        )

    async def _get_staff_slots(
        self,
        staff: Staff,
        business_id: UUID,
        branch_id: UUID,
        target_date: date,
        service_duration: int,
        buffer_before: int,
        buffer_after: int,
    ) -> List[datetime]:
        """Return start times available for a given staff member on a date."""
        total_duration = buffer_before + service_duration + buffer_after
        day_of_week = target_date.weekday()  # 0=Monday

        # 1. Get staff working hours for this day
        wh = await self._get_working_hours("staff", staff.id, day_of_week)
        if not wh or not wh.is_open:
            # Try branch working hours as fallback
            wh = await self._get_working_hours("branch", branch_id, day_of_week)
        if not wh or not wh.is_open:
            return []

        open_dt = self._combine(target_date, wh.open_time)
        close_dt = self._combine(target_date, wh.close_time)
        if open_dt is None or close_dt is None:
            return []

        break_start = self._combine(target_date, wh.break_start) if wh.break_start else None
        break_end = self._combine(target_date, wh.break_end) if wh.break_end else None

        # 2. Check staff leave
        if await self._is_on_leave(staff.id, target_date):
            return []

        # 3. Get existing appointments for this staff on this date
        booked_windows = await self._get_booked_windows(staff.id, target_date)

        # 4. Get temporarily locked slots from Redis
        locked_windows = await self._get_locked_windows(str(staff.id), str(target_date))

        blocked = booked_windows + locked_windows

        # 5. Generate candidate slots on 15-min grid
        candidates: List[datetime] = []
        cursor = open_dt
        while cursor + timedelta(minutes=total_duration) <= close_dt:
            slot_end = cursor + timedelta(minutes=total_duration)
            # Skip if overlaps break
            if break_start and break_end:
                if not (slot_end <= break_start or cursor >= break_end):
                    cursor += timedelta(minutes=SLOT_INTERVAL_MINUTES)
                    continue
            # Skip if overlaps any booked/locked window
            if self._overlaps_any(cursor, slot_end, blocked):
                cursor += timedelta(minutes=SLOT_INTERVAL_MINUTES)
                continue
            # Skip past times for today
            now = datetime.now(timezone.utc)
            if cursor <= now:
                cursor += timedelta(minutes=SLOT_INTERVAL_MINUTES)
                continue

            candidates.append(cursor)
            cursor += timedelta(minutes=SLOT_INTERVAL_MINUTES)

        return candidates

    async def acquire_slot_lock(
        self,
        staff_id: UUID,
        start_time: datetime,
        duration_minutes: int,
    ) -> str:
        """
        Temporarily lock a slot for up to SLOT_LOCK_TTL_SECONDS seconds.
        Returns lock key for confirmation/release.
        Raises SlotUnavailableError if already locked or booked.
        """
        lock_key = f"slot:{staff_id}:{start_time.isoformat()}"
        acquired = await self.redis.set(
            lock_key, "locked",
            nx=True,
            ex=settings.SLOT_LOCK_TTL_SECONDS,
        )
        if not acquired:
            raise SlotUnavailableError("This slot was just taken. Please choose another.")
        return lock_key

    async def release_slot_lock(self, lock_key: str) -> None:
        await self.redis.delete(lock_key)

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _get_service(self, business_id: UUID, service_id: UUID) -> Service:
        result = await self.db.execute(
            select(Service).where(
                Service.id == service_id,
                Service.business_id == business_id,
                Service.deleted_at.is_(None),
                Service.is_active.is_(True),
            )
        )
        svc = result.scalar_one_or_none()
        if not svc:
            raise NotFoundError("Service", service_id)
        return svc

    async def _get_eligible_staff(
        self,
        business_id: UUID,
        branch_id: UUID,
        service_id: UUID,
        staff_id: Optional[UUID],
    ) -> List[Staff]:
        from app.models.staff import StaffStatus
        q = (
            select(Staff)
            .join(StaffServiceModel, StaffServiceModel.staff_id == Staff.id)
            .where(
                Staff.business_id == business_id,
                Staff.deleted_at.is_(None),
                Staff.status == StaffStatus.ACTIVE,
                Staff.bookable.is_(True),
                StaffServiceModel.service_id == service_id,
            )
        )
        # If branch filter
        if branch_id:
            q = q.where(and_(
                (Staff.branch_id == branch_id) | Staff.branch_id.is_(None)
            ))
        if staff_id:
            q = q.where(Staff.id == staff_id)

        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def _get_working_hours(
        self, entity_type: str, entity_id: UUID, day_of_week: int
    ) -> Optional[WorkingHours]:
        result = await self.db.execute(
            select(WorkingHours).where(
                WorkingHours.entity_type == entity_type,
                WorkingHours.entity_id == entity_id,
                WorkingHours.day_of_week == day_of_week,
            )
        )
        return result.scalar_one_or_none()

    async def _is_on_leave(self, staff_id: UUID, target_date: date) -> bool:
        date_str = target_date.isoformat()
        result = await self.db.execute(
            select(StaffLeave).where(
                StaffLeave.staff_id == staff_id,
                StaffLeave.approved.is_(True),
                StaffLeave.start_date <= date_str,
                StaffLeave.end_date >= date_str,
            )
        )
        return result.scalar_one_or_none() is not None

    async def _get_booked_windows(
        self, staff_id: UUID, target_date: date
    ) -> List[Tuple[datetime, datetime]]:
        day_start = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max).replace(tzinfo=timezone.utc)

        result = await self.db.execute(
            select(AppointmentItem.start_time, AppointmentItem.end_time)
            .join(Appointment, Appointment.id == AppointmentItem.appointment_id)
            .where(
                AppointmentItem.staff_id == staff_id,
                AppointmentItem.start_time >= day_start,
                AppointmentItem.start_time <= day_end,
                Appointment.status.in_([
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.PENDING,
                    AppointmentStatus.IN_PROGRESS,
                ]),
            )
        )
        return [(r.start_time, r.end_time) for r in result.all()]

    async def _get_locked_windows(
        self, staff_id: str, date_str: str
    ) -> List[Tuple[datetime, datetime]]:
        pattern = f"slot:{staff_id}:*"
        windows = []
        async for key in self.redis.scan_iter(match=pattern):
            # key format: slot:{staff_id}:{iso_datetime}
            parts = key.split(":", 2)
            if len(parts) == 3:
                try:
                    start = datetime.fromisoformat(parts[2])
                    if start.date().isoformat() == date_str:
                        # We don't know duration here, assume 2 hours max as buffer
                        end = start + timedelta(hours=2)
                        windows.append((start, end))
                except ValueError:
                    pass
        return windows

    @staticmethod
    def _combine(d: date, time_str: Optional[str]) -> Optional[datetime]:
        if not time_str:
            return None
        try:
            h, m = map(int, time_str.split(":"))
            return datetime.combine(d, time(h, m), tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _overlaps_any(
        start: datetime, end: datetime, windows: List[Tuple[datetime, datetime]]
    ) -> bool:
        for ws, we in windows:
            if start < we and end > ws:
                return True
        return False
