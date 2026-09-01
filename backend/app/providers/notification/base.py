"""
Notification provider interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class NotificationMessage:
    recipient: str          # email, phone number, device token, etc.
    body: str
    subject: Optional[str] = None  # for email
    html_body: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class NotificationResult:
    success: bool
    provider_message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider(ABC):
    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult: ...


class SMSProvider(ABC):
    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult: ...


class WhatsAppProvider(ABC):
    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult: ...


class PushProvider(ABC):
    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult: ...
