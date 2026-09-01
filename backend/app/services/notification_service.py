"""
NotificationService — sends notifications via configured providers
and persists a log record for each.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from app.providers.notification.base import NotificationMessage
from app.providers.notification.factory import (
    get_email_provider,
    get_push_provider,
    get_sms_provider,
    get_whatsapp_provider,
)

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        notification_type: NotificationType,
        user_id: Optional[UUID] = None,
        business_id: Optional[UUID] = None,
        html_body: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> Notification:
        provider = get_email_provider()
        message = NotificationMessage(
            recipient=recipient, subject=subject, body=body, html_body=html_body
        )
        result = await provider.send(message)
        return await self._persist(
            channel=NotificationChannel.EMAIL,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            body=body,
            success=result.success,
            error=result.error,
            user_id=user_id,
            business_id=business_id,
            reference_id=reference_id,
        )

    async def send_sms(
        self,
        recipient: str,
        body: str,
        notification_type: NotificationType,
        user_id: Optional[UUID] = None,
        business_id: Optional[UUID] = None,
        reference_id: Optional[str] = None,
    ) -> Notification:
        provider = get_sms_provider()
        message = NotificationMessage(recipient=recipient, subject=None, body=body)
        result = await provider.send(message)
        return await self._persist(
            channel=NotificationChannel.SMS,
            notification_type=notification_type,
            recipient=recipient,
            subject=None,
            body=body,
            success=result.success,
            error=result.error,
            user_id=user_id,
            business_id=business_id,
            reference_id=reference_id,
        )

    async def send_appointment_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        business_name: str,
        appointment_date: str,
        appointment_time: str,
        service_names: str,
        user_id: UUID,
        business_id: UUID,
        appointment_id: UUID,
    ) -> None:
        body = f"""
Hi {customer_name},

Your appointment has been confirmed!

Business: {business_name}
Date: {appointment_date}
Time: {appointment_time}
Services: {service_names}

Thank you for booking with Zenglow.
        """.strip()

        await self.send_email(
            recipient=customer_email,
            subject=f"Appointment Confirmed — {business_name}",
            body=body,
            notification_type=NotificationType.APPOINTMENT_CONFIRMED,
            user_id=user_id,
            business_id=business_id,
            reference_id=str(appointment_id),
        )

    async def send_reminder(
        self,
        customer_email: str,
        customer_name: str,
        business_name: str,
        appointment_date: str,
        appointment_time: str,
        hours_before: int,
        user_id: UUID,
        business_id: UUID,
        appointment_id: UUID,
    ) -> None:
        ntype = (
            NotificationType.APPOINTMENT_REMINDER_24H
            if hours_before == 24
            else NotificationType.APPOINTMENT_REMINDER_2H
        )
        body = f"""
Hi {customer_name},

Reminder: Your appointment at {business_name} is in {hours_before} hours.

Date: {appointment_date}
Time: {appointment_time}

See you soon!
        """.strip()

        await self.send_email(
            recipient=customer_email,
            subject=f"Appointment Reminder — {business_name}",
            body=body,
            notification_type=ntype,
            user_id=user_id,
            business_id=business_id,
            reference_id=str(appointment_id),
        )

    async def _persist(
        self,
        channel: NotificationChannel,
        notification_type: NotificationType,
        recipient: str,
        subject: Optional[str],
        body: str,
        success: bool,
        error: Optional[str] = None,
        user_id: Optional[UUID] = None,
        business_id: Optional[UUID] = None,
        reference_id: Optional[str] = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            business_id=business_id,
            channel=channel,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            body=body,
            status=NotificationStatus.SENT if success else NotificationStatus.FAILED,
            error_message=error,
            sent_at=datetime.now(timezone.utc) if success else None,
            reference_id=reference_id,
        )
        self.db.add(notif)
        await self.db.flush()
        return notif
