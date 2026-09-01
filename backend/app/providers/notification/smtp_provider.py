"""
SMTP email provider.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.notification.base import EmailProvider, NotificationMessage, NotificationResult

logger = get_logger(__name__)


class SMTPEmailProvider(EmailProvider):
    async def send(self, message: NotificationMessage) -> NotificationResult:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject or "Notification from Zenglow"
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            msg["To"] = message.recipient

            msg.attach(MIMEText(message.body, "plain"))
            if message.html_body:
                msg.attach(MIMEText(message.html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, message.recipient, msg.as_string())

            return NotificationResult(success=True)
        except Exception as e:
            logger.error("smtp_send_failed", error=str(e), recipient=message.recipient)
            return NotificationResult(success=False, error=str(e))
