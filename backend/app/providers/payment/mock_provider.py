"""
Mock payment provider for development/testing.
Always succeeds — never use in production.
"""
import uuid
from typing import Optional

from app.core.logging import get_logger
from app.providers.payment.base import (
    PaymentCapture,
    PaymentOrder,
    PaymentProvider,
    RefundResult,
)

logger = get_logger(__name__)


class MockPaymentProvider(PaymentProvider):
    """
    Development mock provider.
    Simulates payment lifecycle without real charges.
    """

    async def create_order(self, amount: float, currency: str, metadata: dict) -> PaymentOrder:
        order_id = f"mock_order_{uuid.uuid4().hex[:16]}"
        logger.info("mock_payment_order_created", order_id=order_id, amount=amount)
        return PaymentOrder(
            provider_order_id=order_id,
            amount=amount,
            currency=currency,
            provider_data={"id": order_id, "status": "created", "mock": True},
        )

    async def verify_payment(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        provider_signature: str,
    ) -> bool:
        # In development, accept any "mock_" prefixed IDs
        return provider_payment_id.startswith("mock_")

    async def capture_payment(self, provider_payment_id: str, amount: float) -> PaymentCapture:
        return PaymentCapture(
            provider_payment_id=provider_payment_id,
            provider_order_id=f"mock_order_{uuid.uuid4().hex[:8]}",
            provider_signature="mock_sig",
            captured=True,
            amount=amount,
            provider_data={"status": "captured", "mock": True},
        )

    async def process_refund(
        self,
        provider_payment_id: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> RefundResult:
        refund_id = f"mock_refund_{uuid.uuid4().hex[:16]}"
        return RefundResult(
            provider_refund_id=refund_id,
            status="processed",
            amount=amount,
            provider_data={"id": refund_id, "mock": True},
        )

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        return True  # Accept all mock webhooks
