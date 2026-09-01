"""
Celery tasks — all tasks must be idempotent.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from celery import Task
from sqlalchemy import select

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.workers.tasks.send_booking_confirmation",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_booking_confirmation(self: Task, appointment_id: str, customer_id: str) -> dict:
    """Send booking confirmation email and SMS to customer."""
    logger.info("task_send_booking_confirmation", appointment_id=appointment_id)
    try:
        return _run_async(_send_booking_confirmation_async(appointment_id, customer_id))
    except Exception as exc:
        logger.error("task_failed", task="send_booking_confirmation", error=str(exc))
        raise self.retry(exc=exc)


async def _send_booking_confirmation_async(appointment_id: str, customer_id: str) -> dict:
    from app.db.session import get_db_context
    from app.models.appointment import Appointment
    from app.models.business import Business
    from app.models.customer import Customer
    from app.models.user import User
    from app.services.notification_service import NotificationService

    async with get_db_context() as db:
        result = await db.execute(
            select(Appointment).where(Appointment.id == UUID(appointment_id))
        )
        appointment = result.scalar_one_or_none()
        if not appointment:
            return {"status": "skipped", "reason": "appointment_not_found"}

        result = await db.execute(
            select(Customer).where(Customer.id == appointment.customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return {"status": "skipped", "reason": "customer_not_found"}

        result = await db.execute(select(User).where(User.id == customer.user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {"status": "skipped", "reason": "user_not_found"}

        result = await db.execute(select(Business).where(Business.id == appointment.business_id))
        business = result.scalar_one_or_none()

        svc = NotificationService(db)
        await svc.send_appointment_confirmation(
            customer_email=user.email,
            customer_name=user.full_name,
            business_name=business.name if business else "Zenglow Business",
            appointment_date=appointment.start_time.strftime("%B %d, %Y"),
            appointment_time=appointment.start_time.strftime("%I:%M %p"),
            service_names="Your booked services",
            user_id=user.id,
            business_id=appointment.business_id,
            appointment_id=appointment.id,
        )
        return {"status": "sent"}


@celery_app.task(
    name="app.workers.tasks.send_appointment_reminders",
    bind=True,
    max_retries=2,
)
def send_appointment_reminders(self: Task, hours_before: int) -> dict:
    """Send appointment reminders for upcoming appointments."""
    logger.info("task_send_reminders", hours_before=hours_before)
    try:
        return _run_async(_send_reminders_async(hours_before))
    except Exception as exc:
        logger.error("task_failed", task="send_appointment_reminders", error=str(exc))
        raise self.retry(exc=exc)


async def _send_reminders_async(hours_before: int) -> dict:
    from app.db.session import get_db_context
    from app.models.appointment import Appointment, AppointmentStatus
    from app.models.customer import Customer
    from app.models.business import Business
    from app.models.user import User
    from app.services.notification_service import NotificationService

    now = datetime.now(timezone.utc)
    window_start = now + timedelta(hours=hours_before) - timedelta(minutes=15)
    window_end = now + timedelta(hours=hours_before) + timedelta(minutes=15)

    sent_count = 0
    async with get_db_context() as db:
        field = "reminder_24h_sent" if hours_before == 24 else "reminder_2h_sent"
        result = await db.execute(
            select(Appointment).where(
                Appointment.start_time.between(window_start, window_end),
                Appointment.status == AppointmentStatus.CONFIRMED,
                Appointment.deleted_at.is_(None),
            )
        )
        appointments = result.scalars().all()

        for appt in appointments:
            # Check idempotency
            if hours_before == 24 and appt.reminder_24h_sent:
                continue
            if hours_before == 2 and appt.reminder_2h_sent:
                continue

            result2 = await db.execute(select(Customer).where(Customer.id == appt.customer_id))
            customer = result2.scalar_one_or_none()
            if not customer:
                continue

            result3 = await db.execute(select(User).where(User.id == customer.user_id))
            user = result3.scalar_one_or_none()
            if not user:
                continue

            result4 = await db.execute(select(Business).where(Business.id == appt.business_id))
            business = result4.scalar_one_or_none()

            svc = NotificationService(db)
            await svc.send_reminder(
                customer_email=user.email,
                customer_name=user.full_name,
                business_name=business.name if business else "Zenglow Business",
                appointment_date=appt.start_time.strftime("%B %d, %Y"),
                appointment_time=appt.start_time.strftime("%I:%M %p"),
                hours_before=hours_before,
                user_id=user.id,
                business_id=appt.business_id,
                appointment_id=appt.id,
            )

            # Mark reminder as sent
            if hours_before == 24:
                appt.reminder_24h_sent = True
            else:
                appt.reminder_2h_sent = True
            db.add(appt)
            sent_count += 1

    return {"status": "done", "sent": sent_count}


@celery_app.task(name="app.workers.tasks.reconcile_payments", bind=True)
def reconcile_payments(self: Task) -> dict:
    """Reconcile PENDING payments older than 30 minutes — mark as failed if unresolved."""
    logger.info("task_reconcile_payments")
    try:
        return _run_async(_reconcile_payments_async())
    except Exception as exc:
        logger.error("task_failed", task="reconcile_payments", error=str(exc))
        raise self.retry(exc=exc)


async def _reconcile_payments_async() -> dict:
    from app.db.session import get_db_context
    from app.models.payment import Payment, PaymentStatus

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    updated = 0

    async with get_db_context() as db:
        result = await db.execute(
            select(Payment).where(
                Payment.status == PaymentStatus.PENDING,
                Payment.created_at < cutoff,
            )
        )
        payments = result.scalars().all()
        for payment in payments:
            payment.status = PaymentStatus.CANCELLED
            payment.failure_reason = "Payment session expired (auto-reconciled)"
            db.add(payment)
            updated += 1

    return {"status": "done", "updated": updated}


@celery_app.task(name="app.workers.tasks.send_review_requests", bind=True)
def send_review_requests(self: Task) -> dict:
    """Send review request emails for completed appointments from yesterday."""
    logger.info("task_send_review_requests")
    try:
        return _run_async(_send_review_requests_async())
    except Exception as exc:
        logger.error("task_failed", task="send_review_requests", error=str(exc))
        raise self.retry(exc=exc)


async def _send_review_requests_async() -> dict:
    from app.db.session import get_db_context
    from app.models.appointment import Appointment, AppointmentStatus
    from app.models.customer import Customer
    from app.models.business import Business
    from app.models.user import User
    from app.services.notification_service import NotificationService
    from app.models.notification import NotificationType

    yesterday_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=1)
    yesterday_end = yesterday_start + timedelta(days=1)
    sent_count = 0

    async with get_db_context() as db:
        result = await db.execute(
            select(Appointment).where(
                Appointment.status == AppointmentStatus.COMPLETED,
                Appointment.end_time.between(yesterday_start, yesterday_end),
                Appointment.deleted_at.is_(None),
            )
        )
        appointments = result.scalars().all()

        for appt in appointments:
            result2 = await db.execute(select(Customer).where(Customer.id == appt.customer_id))
            customer = result2.scalar_one_or_none()
            if not customer:
                continue
            result3 = await db.execute(select(User).where(User.id == customer.user_id))
            user = result3.scalar_one_or_none()
            if not user:
                continue
            result4 = await db.execute(select(Business).where(Business.id == appt.business_id))
            business = result4.scalar_one_or_none()

            svc = NotificationService(db)
            await svc.send_email(
                recipient=user.email,
                subject=f"How was your experience at {business.name if business else 'Zenglow'}?",
                body=f"Hi {user.full_name},\n\nWe hope you enjoyed your visit. Please leave a review!\n\nThank you,\nZenglow Team",
                notification_type=NotificationType.REVIEW_REQUEST,
                user_id=user.id,
                business_id=appt.business_id,
                reference_id=str(appt.id),
            )
            sent_count += 1

    return {"status": "done", "sent": sent_count}
