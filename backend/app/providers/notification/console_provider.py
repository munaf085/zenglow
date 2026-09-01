"""
Console notification provider — logs messages instead of sending.
Used in development and testing.
"""
from app.core.logging import get_logger
from app.providers.notification.base import (
    EmailProvider,
    NotificationMessage,
    NotificationResult,
    PushProvider,
    SMSProvider,
    WhatsAppProvider,
)

logger = get_logger(__name__)


class ConsoleEmailProvider(EmailProvider):
    async def send(self, message: NotificationMessage) -> NotificationResult:
        logger.info(
            "📧 [EMAIL]",
            to=message.recipient,
            subject=message.subject,
            body=message.body[:100],
        )
        return NotificationResult(success=True, provider_message_id="console-email")


class ConsoleSMSProvider(SMSProvider):
    async def send(self, message: NotificationMessage) -> NotificationResult:
        logger.info("📱 [SMS]", to=message.recipient, body=message.body[:100])
        return NotificationResult(success=True, provider_message_id="console-sms")


class ConsoleWhatsAppProvider(WhatsAppProvider):
    async def send(self, message: NotificationMessage) -> NotificationResult:
        logger.info("💬 [WHATSAPP]", to=message.recipient, body=message.body[:100])
        return NotificationResult(success=True, provider_message_id="console-whatsapp")


class ConsolePushProvider(PushProvider):
    async def send(self, message: NotificationMessage) -> NotificationResult:
        logger.info("🔔 [PUSH]", to=message.recipient, body=message.body[:100])
        return NotificationResult(success=True, provider_message_id="console-push")
