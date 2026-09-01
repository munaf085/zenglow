"""
Notification provider factory.
Resolves the correct provider from environment configuration.
Development default: console (logs to stdout — no external deps needed).
"""
from app.core.config import settings
from app.providers.notification.base import (
    EmailProvider,
    PushProvider,
    SMSProvider,
    WhatsAppProvider,
)


def get_email_provider() -> EmailProvider:
    provider = settings.EMAIL_PROVIDER.lower()
    if provider == "smtp":
        from app.providers.notification.smtp_provider import SMTPEmailProvider
        return SMTPEmailProvider()
    # Default: console (logs to stdout)
    from app.providers.notification.console_provider import ConsoleEmailProvider
    return ConsoleEmailProvider()


def get_sms_provider() -> SMSProvider:
    provider = settings.SMS_PROVIDER.lower()
    if provider == "twilio":
        from app.providers.notification.twilio_provider import TwilioSMSProvider
        return TwilioSMSProvider()
    from app.providers.notification.console_provider import ConsoleSMSProvider
    return ConsoleSMSProvider()


def get_whatsapp_provider() -> WhatsAppProvider:
    provider = settings.WHATSAPP_PROVIDER.lower()
    if provider == "twilio":
        from app.providers.notification.twilio_provider import TwilioWhatsAppProvider
        return TwilioWhatsAppProvider()
    from app.providers.notification.console_provider import ConsoleWhatsAppProvider
    return ConsoleWhatsAppProvider()


def get_push_provider() -> PushProvider:
    provider = settings.PUSH_PROVIDER.lower()
    if provider == "firebase":
        # Firebase FCM — Phase 5 (native mobile apps)
        # Provider implementation added when mobile app development begins
        from app.providers.notification.console_provider import ConsolePushProvider
        return ConsolePushProvider()
    from app.providers.notification.console_provider import ConsolePushProvider
    return ConsolePushProvider()
