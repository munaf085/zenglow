"""
Twilio SMS and WhatsApp provider.

SMS:    Uses Twilio Programmable SMS API
WhatsApp: Uses Twilio's WhatsApp Business API (sandbox or production)

Configuration:
  TWILIO_ACCOUNT_SID   — your Twilio Account SID
  TWILIO_AUTH_TOKEN    — your Twilio Auth Token
  TWILIO_FROM_NUMBER   — SMS sender number (e.g. +14155552671)
  TWILIO_WHATSAPP_FROM — WhatsApp sender (e.g. whatsapp:+14155238886)
"""
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.notification.base import (
    NotificationMessage,
    NotificationResult,
    SMSProvider,
    WhatsAppProvider,
)

logger = get_logger(__name__)


def _get_twilio_client():
    """Lazy-load Twilio client — only imported if Twilio is configured."""
    try:
        from twilio.rest import Client  # type: ignore
        return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    except ImportError:
        raise RuntimeError(
            "twilio package not installed. Run: pip install twilio"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Twilio client: {e}")


class TwilioSMSProvider(SMSProvider):
    """
    Sends SMS messages via Twilio Programmable SMS.
    Recipient must be E.164 format (e.g. +919876543210).
    """

    async def send(self, message: NotificationMessage) -> NotificationResult:
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.error("twilio_sms_not_configured")
            return NotificationResult(success=False, error="Twilio credentials not configured")

        try:
            client = _get_twilio_client()
            msg = client.messages.create(
                body=message.body,
                from_=settings.TWILIO_FROM_NUMBER,
                to=message.recipient,
            )
            logger.info(
                "twilio_sms_sent",
                to=message.recipient,
                sid=msg.sid,
                status=msg.status,
            )
            return NotificationResult(success=True, provider_message_id=msg.sid)
        except Exception as e:
            logger.error("twilio_sms_failed", to=message.recipient, error=str(e))
            return NotificationResult(success=False, error=str(e))


class TwilioWhatsAppProvider(WhatsAppProvider):
    """
    Sends WhatsApp messages via Twilio's WhatsApp Business API.

    For sandbox (testing): prefix numbers with 'whatsapp:'
    Twilio sandbox number: whatsapp:+14155238886

    For production: use your approved WhatsApp Business number.
    Recipients must have opted in to receive WhatsApp messages.

    Message templates are required for outbound messages outside
    the 24-hour customer service window.
    """

    WHATSAPP_PREFIX = "whatsapp:"

    def _format_number(self, number: str) -> str:
        if not number.startswith(self.WHATSAPP_PREFIX):
            return f"{self.WHATSAPP_PREFIX}{number}"
        return number

    async def send(self, message: NotificationMessage) -> NotificationResult:
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.error("twilio_whatsapp_not_configured")
            return NotificationResult(
                success=False, error="Twilio credentials not configured"
            )

        from_number = getattr(settings, "TWILIO_WHATSAPP_FROM", None) or (
            f"{self.WHATSAPP_PREFIX}{settings.TWILIO_FROM_NUMBER}"
            if settings.TWILIO_FROM_NUMBER
            else None
        )

        if not from_number:
            return NotificationResult(
                success=False, error="TWILIO_WHATSAPP_FROM not configured"
            )

        try:
            client = _get_twilio_client()
            msg = client.messages.create(
                body=message.body,
                from_=self._format_number(from_number),
                to=self._format_number(message.recipient),
            )
            logger.info(
                "twilio_whatsapp_sent",
                to=message.recipient,
                sid=msg.sid,
                status=msg.status,
            )
            return NotificationResult(success=True, provider_message_id=msg.sid)
        except Exception as e:
            logger.error(
                "twilio_whatsapp_failed", to=message.recipient, error=str(e)
            )
            return NotificationResult(success=False, error=str(e))
