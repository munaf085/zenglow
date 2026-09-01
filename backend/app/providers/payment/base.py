"""
Payment provider interface. All providers must implement this.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentOrder:
    provider_order_id: str
    amount: float
    currency: str
    provider_data: dict  # raw provider response


@dataclass
class PaymentCapture:
    provider_payment_id: str
    provider_order_id: str
    provider_signature: Optional[str]
    captured: bool
    amount: float
    provider_data: dict


@dataclass
class RefundResult:
    provider_refund_id: str
    status: str
    amount: float
    provider_data: dict


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    @abstractmethod
    async def create_order(self, amount: float, currency: str, metadata: dict) -> PaymentOrder:
        """Create a payment order and return provider order details."""
        ...

    @abstractmethod
    async def verify_payment(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        provider_signature: str,
    ) -> bool:
        """Verify payment authenticity. Returns True if valid."""
        ...

    @abstractmethod
    async def capture_payment(
        self,
        provider_payment_id: str,
        amount: float,
    ) -> PaymentCapture:
        """Capture/confirm a payment."""
        ...

    @abstractmethod
    async def process_refund(
        self,
        provider_payment_id: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> RefundResult:
        """Initiate a refund."""
        ...

    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook request authenticity."""
        ...
