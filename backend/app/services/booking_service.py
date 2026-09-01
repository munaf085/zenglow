"""
BookingService — appointment creation with slot locking and double-booking prevention.

Flow:
  1. Validate business + branch + service
  2. Determine booking source (DIRECT vs MARKETPLACE) — critical for commission
  3. Find eligible staff (or pick requested staff)
  4. Acquire Redis slot lock (prevents race condition)
  5. Check for real database conflicts within a transaction
  6. Create appointment + items with source attribution
  7. Calculate marketplace commission if applicable
  8. Release lock
  9. Queue notifications
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BusinessRuleError,
    NotFoundError,
    SlotUnavailableError,
    TenantIsolationError,
)
from app.core.logging import get_logger
from app.models.appointment import (
    APPOINTMENT_TRANSITIONS,
    Appointment,
    AppointmentItem,
    AppointmentSource,
    AppointmentStatus,
    MARKETPLACE_SOURCES,
    is_marketplace_booking,
)
from app.models.business import Branch, Business, BusinessStatus
from app.models.customer import Customer
from app.models.service import Service
from app.models.staff import Staff, StaffService as StaffServiceModel
from app.models.user import User
from app.schemas.booking import (
    AppointmentResponse,
    BookingItemRequest,
    CancelBookingRequest,
    CreateBookingRequest,
)
from app.services.availability_service import AvailabilityService

# Default marketplace commission rate — in production this comes from the subscription plan
DEFAULT_MARKETPLACE_COMMISSION_RATE = 0.0500  # 5%
logger = get_logger(__name__)


class BookingService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis
        self.availability_svc = AvailabilityService(db, redis)

    async def create_booking(
        self, data: CreateBookingRequest, user: User
    ) -> Appointment:
        """Create a booking with slot locking. Transactional."""

        # Validate business is active
        business = await self._get_active_business(data.business_id)
        branch = await self._get_active_branch(data.business_id, data.branch_id)
        customer = await self._get_customer(user.id)

        lock_keys: List[str] = []
        appointment_items_data = []

        try:
            for item_req in data.items:
                service = await self._get_bookable_service(data.business_id, item_req.service_id)
                staff = await self._resolve_staff(
                    data.business_id, data.branch_id, item_req.service_id, item_req.staff_id
                )

                # Compute actual end time including buffers
                total_minutes = (
                    service.buffer_before_minutes
                    + service.duration_minutes
                    + service.buffer_after_minutes
                )
                start_time = item_req.start_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)

                # Cannot book in the past
                if start_time <= datetime.now(timezone.utc):
                    raise BusinessRuleError("Cannot book a slot in the past")

                end_time = start_time + timedelta(minutes=total_minutes)

                # Service start time adjusted for buffer
                item_start = start_time + timedelta(minutes=service.buffer_before_minutes)
                item_end = item_start + timedelta(minutes=service.duration_minutes)

                # 1. Acquire Redis lock (prevents concurrent race conditions)
                lock_key = await self.availability_svc.acquire_slot_lock(
                    staff.id, start_time, total_minutes
                )
                lock_keys.append(lock_key)

                # 2. Double-check DB for conflicts within the transaction
                has_conflict = await self._has_appointment_conflict(
                    staff.id, item_start, item_end
                )
                if has_conflict:
                    raise SlotUnavailableError(
                        f"Staff {staff.full_name} is not available at this time"
                    )

                appointment_items_data.append({
                    "service": service,
                    "staff": staff,
                    "item_start": item_start,
                    "item_end": item_end,
                    "price": float(service.price),
                    "tax_rate": float(service.tax_rate),
                    "duration_minutes": service.duration_minutes,
                })

            # 3. Build appointment
            all_starts = [d["item_start"] for d in appointment_items_data]
            all_ends = [d["item_end"] for d in appointment_items_data]
            appt_start = min(all_starts)
            appt_end = max(all_ends)

            subtotal = sum(d["price"] for d in appointment_items_data)
            tax_amount = sum(
                d["price"] * d["tax_rate"] / 100 for d in appointment_items_data
            )
            total_amount = subtotal + tax_amount

            deposit_amount = 0.0
            initial_status = AppointmentStatus.CONFIRMED
            if business.deposit_required and business.deposit_percentage:
                deposit_amount = round(total_amount * float(business.deposit_percentage) / 100, 2)
                if deposit_amount > 0:
                    initial_status = AppointmentStatus.PENDING

            # ── Source attribution & commission ───────────────────────────────
            source = getattr(data, "source", AppointmentSource.ONLINE)
            is_marketplace = is_marketplace_booking(source)

            # Check if this is the customer's first booking with this business
            # (determines commission eligibility for marketplace bookings)
            is_new_customer = False
            if is_marketplace:
                prev_booking = await self._get_previous_booking(
                    customer.id, data.business_id
                )
                is_new_customer = prev_booking is None

            # Commission applies only to marketplace bookings with a new customer
            commission_rate: Optional[float] = None
            commission_amount: Optional[float] = None
            if is_marketplace and is_new_customer:
                commission_rate = DEFAULT_MARKETPLACE_COMMISSION_RATE
                commission_amount = round(total_amount * commission_rate, 2)
                logger.info(
                    "marketplace_commission_calculated",
                    business_id=str(data.business_id),
                    customer_id=str(customer.id),
                    total_amount=total_amount,
                    commission_amount=commission_amount,
                )

            appointment = Appointment(
                business_id=data.business_id,
                branch_id=data.branch_id,
                customer_id=customer.id,
                start_time=appt_start,
                end_time=appt_end,
                status=initial_status,
                source=source,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                deposit_amount=deposit_amount,
                customer_notes=data.customer_notes,
                # Marketplace attribution
                is_marketplace_booking=is_marketplace,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                commission_paid=False,
                is_new_customer_via_marketplace=is_new_customer,
            )
            self.db.add(appointment)
            await self.db.flush()

            for item_data in appointment_items_data:
                item = AppointmentItem(
                    appointment_id=appointment.id,
                    service_id=item_data["service"].id,
                    staff_id=item_data["staff"].id,
                    service_name=item_data["service"].name,
                    duration_minutes=item_data["duration_minutes"],
                    price=item_data["price"],
                    tax_rate=item_data["tax_rate"],
                    start_time=item_data["item_start"],
                    end_time=item_data["item_end"],
                )
                self.db.add(item)

            await self.db.flush()
            await self.db.refresh(appointment, ["items"])

            # 4. Release locks now that appointment is persisted
            for lock_key in lock_keys:
                await self.availability_svc.release_slot_lock(lock_key)

            logger.info(
                "booking_created",
                appointment_id=str(appointment.id),
                customer_id=str(customer.id),
                business_id=str(data.business_id),
            )

            # 5. Queue notifications asynchronously (fire-and-forget)
            self._queue_booking_notifications(appointment.id, customer.id)

            return appointment

        except Exception:
            # Release all acquired locks on failure
            for lock_key in lock_keys:
                await self.availability_svc.release_slot_lock(lock_key)
            raise

    async def cancel_booking(
        self, appointment_id: UUID, user: User, data: CancelBookingRequest
    ) -> Appointment:
        appointment = await self._get_appointment_for_user(appointment_id, user)

        if appointment.status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        ]:
            raise BusinessRuleError(f"Cannot cancel a {appointment.status.value} appointment")

        now = datetime.now(timezone.utc)

        # Enforce cancellation policy checks
        business = await self._get_active_business(appointment.business_id)
        cancellation_hours = business.cancellation_hours if business.cancellation_hours is not None else 24

        appt_start = appointment.start_time
        if appt_start.tzinfo is None:
            appt_start = appt_start.replace(tzinfo=timezone.utc)

        hours_before = (appt_start - now).total_seconds() / 3600.0
        is_late_cancellation = hours_before < cancellation_hours

        logger.info(
            "appointment_cancelled",
            appointment_id=str(appointment.id),
            hours_before=hours_before,
            cancellation_window_hours=cancellation_hours,
            is_late=is_late_cancellation,
            user_id=str(user.id),
        )

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = now
        appointment.cancel_reason = data.reason
        appointment.cancelled_by_id = user.id
        self.db.add(appointment)
        await self.db.flush()
        return appointment

    async def get_appointment(self, appointment_id: UUID, user: User) -> Appointment:
        return await self._get_appointment_for_user(appointment_id, user)

    async def list_customer_appointments(
        self, user: User, status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        customer = await self._get_customer(user.id)
        q = (
            select(Appointment)
            .options(selectinload(Appointment.items))
            .where(
                Appointment.customer_id == customer.id,
                Appointment.deleted_at.is_(None),
            )
        )
        if status:
            q = q.where(Appointment.status == status)
        q = q.order_by(Appointment.start_time.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def list_business_appointments(
        self,
        business_id: UUID,
        branch_id: Optional[UUID] = None,
        staff_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[AppointmentStatus] = None,
        user: Optional[User] = None,
    ) -> List[Appointment]:
        from app.core.deps import assert_business_access
        if user:
            assert_business_access(user, business_id)

        q = (
            select(Appointment)
            .options(selectinload(Appointment.items))
            .where(
                Appointment.business_id == business_id,
                Appointment.deleted_at.is_(None),
            )
        )
        if branch_id:
            q = q.where(Appointment.branch_id == branch_id)
        if start_date:
            q = q.where(Appointment.start_time >= start_date)
        if end_date:
            q = q.where(Appointment.start_time <= end_date)
        if status:
            q = q.where(Appointment.status == status)
        if staff_id:
            q = q.join(AppointmentItem, AppointmentItem.appointment_id == Appointment.id).where(
                AppointmentItem.staff_id == staff_id
            )

        q = q.order_by(Appointment.start_time)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def update_appointment_status(
        self, appointment_id: UUID, status: AppointmentStatus, user: User
    ) -> Appointment:
        from app.core.deps import assert_business_access
        result = await self.db.execute(
            select(Appointment)
            .options(selectinload(Appointment.items))
            .where(
                Appointment.id == appointment_id,
                Appointment.deleted_at.is_(None),
            )
        )
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise NotFoundError("Appointment", appointment_id)
        assert_business_access(user, appointment.business_id)

        # Validate state machine transitions
        allowed = APPOINTMENT_TRANSITIONS.get(appointment.status, [])
        if status not in allowed:
            raise BusinessRuleError(
                f"Cannot transition appointment from {appointment.status.value} to {status.value}"
            )

        now = datetime.now(timezone.utc)
        if status == AppointmentStatus.CANCELLED:
            appointment.cancelled_at = now
            appointment.cancelled_by_id = user.id

        appointment.status = status
        self.db.add(appointment)
        await self.db.flush()
        return appointment

    async def confirm_deposit_payment(
        self, appointment_id: UUID, user: User
    ) -> Appointment:
        """Confirm deposit payment and transition PENDING appointment to CONFIRMED."""
        result = await self.db.execute(
            select(Appointment)
            .options(selectinload(Appointment.items))
            .where(
                Appointment.id == appointment_id,
                Appointment.deleted_at.is_(None),
            )
        )
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise NotFoundError("Appointment", appointment_id)

        if appointment.status != AppointmentStatus.PENDING:
            raise BusinessRuleError(
                f"Appointment is not awaiting deposit confirmation (current status: {appointment.status.value})"
            )

        appointment.status = AppointmentStatus.CONFIRMED
        self.db.add(appointment)
        await self.db.flush()
        return appointment

    # ── private helpers ───────────────────────────────────────────────────────

    async def _get_active_business(self, business_id: UUID) -> Business:
        result = await self.db.execute(
            select(Business).where(
                Business.id == business_id,
                Business.status == BusinessStatus.ACTIVE,
                Business.deleted_at.is_(None),
            )
        )
        biz = result.scalar_one_or_none()
        if not biz:
            raise NotFoundError("Business", business_id)
        return biz

    async def _get_active_branch(self, business_id: UUID, branch_id: UUID) -> Branch:
        result = await self.db.execute(
            select(Branch).where(
                Branch.id == branch_id,
                Branch.business_id == business_id,
                Branch.is_active.is_(True),
                Branch.deleted_at.is_(None),
            )
        )
        branch = result.scalar_one_or_none()
        if not branch:
            raise NotFoundError("Branch", branch_id)
        return branch

    async def _get_customer(self, user_id: UUID) -> Customer:
        result = await self.db.execute(
            select(Customer).where(
                Customer.user_id == user_id, Customer.deleted_at.is_(None)
            )
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise NotFoundError("Customer profile", user_id)
        return customer

    async def _get_bookable_service(self, business_id: UUID, service_id: UUID) -> Service:
        result = await self.db.execute(
            select(Service).where(
                Service.id == service_id,
                Service.business_id == business_id,
                Service.is_active.is_(True),
                Service.online_booking_enabled.is_(True),
                Service.deleted_at.is_(None),
            )
        )
        svc = result.scalar_one_or_none()
        if not svc:
            raise NotFoundError("Service", service_id)
        return svc

    async def _resolve_staff(
        self,
        business_id: UUID,
        branch_id: UUID,
        service_id: UUID,
        staff_id: Optional[UUID],
    ) -> Staff:
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
        if staff_id:
            q = q.where(Staff.id == staff_id)

        result = await self.db.execute(q)
        staff_list = list(result.scalars().all())
        if not staff_list:
            raise SlotUnavailableError("No available staff for this service")
        return staff_list[0]

    async def _has_appointment_conflict(
        self, staff_id: UUID, start_time: datetime, end_time: datetime
    ) -> bool:
        """Check if any confirmed/pending appointment item overlaps the window."""
        result = await self.db.execute(
            select(AppointmentItem.id)
            .join(Appointment, Appointment.id == AppointmentItem.appointment_id)
            .where(
                AppointmentItem.staff_id == staff_id,
                Appointment.status.in_([
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.PENDING,
                    AppointmentStatus.IN_PROGRESS,
                ]),
                AppointmentItem.start_time < end_time,
                AppointmentItem.end_time > start_time,
            )
        )
        return result.scalar_one_or_none() is not None

    async def _get_appointment_for_user(self, appointment_id: UUID, user: User) -> Appointment:
        result = await self.db.execute(
            select(Appointment)
            .options(selectinload(Appointment.items))
            .where(
                Appointment.id == appointment_id,
                Appointment.deleted_at.is_(None),
            )
        )
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise NotFoundError("Appointment", appointment_id)

        # Check ownership: either customer's own or business staff
        customer = await self._get_customer(user.id)
        if str(appointment.customer_id) != str(customer.id):
            # Check if user has business access
            from app.core.deps import assert_business_access
            assert_business_access(user, appointment.business_id)
        return appointment

    def _queue_booking_notifications(self, appointment_id: UUID, customer_id: UUID) -> None:
        """Fire-and-forget Celery task for notifications."""
        try:
            from app.workers.tasks import send_booking_confirmation
            send_booking_confirmation.delay(str(appointment_id), str(customer_id))
        except Exception as e:
            logger.warning("notification_queue_failed", error=str(e))

    async def _get_previous_booking(
        self, customer_id: UUID, business_id: UUID
    ) -> Optional[Appointment]:
        """
        Check if customer has any prior booking with this business.
        Used to determine marketplace commission eligibility.
        Commission only applies to NEW customers brought by the marketplace.
        """
        result = await self.db.execute(
            select(Appointment.id)
            .where(
                Appointment.customer_id == customer_id,
                Appointment.business_id == business_id,
                Appointment.status.notin_([AppointmentStatus.CANCELLED]),
                Appointment.deleted_at.is_(None),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
