"""
Razorpay payment provider — production-ready implementation.

Payment flow:
  1. create_order()         → creates Razorpay order, returns order_id for frontend SDK
  2. [frontend]             → customer pays via Razorpay Checkout JS
  3. verify_payment()       → HMAC-SHA256 server-side signature verification (CRITICAL)
  4. capture_payment()      → fetch payment status from Razorpay API
  5. process_refund()       → initiate refund via Razorpay API

Webhook flow:
  POST /payments/webhook    → verify_webhook_signature() first, then process event

NEVER trust frontend-reported payment_id alone.
Always verify the HMAC signature before confirming a booking.
"""
import hashlib
import hmac
import json
from typing import Optional

from app.core.config import settings
from app.core.exceptions import PaymentError
from app.core.logging import get_logger
from app.providers.payment.base import (
    PaymentCapture,
    PaymentOrder,
    PaymentProvider,
    RefundResult,
)

logger = get_logger(__name__)


class RazorpayProvider(PaymentProvider):
    def __init__(self) -> None:
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.key_id or not self.key_secret:
                raise PaymentError(
                    "Razorpay credentials not configured. "
                    "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in environment."
                )
            try:
                import razorpay
                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except ImportError:
                raise PaymentError(
                    "razorpay package not installed. Run: pip install razorpay"
                )
        return self._client

    # ── Order creation ────────────────────────────────────────────────────────

    async def create_order(
        self, amount: float, currency: str, metadata: dict
    ) -> PaymentOrder:
        """
        Create a Razorpay order.
        Amount is in major currency units (e.g. INR rupees, not paise).
        Razorpay requires amount in paise (smallest unit), so we multiply by 100.
        """
        try:
            client = self._get_client()
            amount_paise = int(round(amount * 100))  # Convert to paise
            order_data = {
                "amount": amount_paise,
                "currency": currency,
                "notes": {k: str(v) for k, v in metadata.items()},  # Razorpay notes must be strings
                "payment_capture": 1,  # Auto-capture on payment
            }
            order = client.order.create(data=order_data)
            logger.info(
                "razorpay_order_created",
                order_id=order["id"],
                amount=amount,
                currency=currency,
            )
            return PaymentOrder(
                provider_order_id=order["id"],
                amount=amount,
                currency=currency,
                provider_data=order,
            )
        except PaymentError:
            raise
        except Exception as e:
            logger.error("razorpay_create_order_failed", error=str(e))
            raise PaymentError(f"Failed to create Razorpay order: {e}")

    # ── Signature verification (CRITICAL — never skip this) ───────────────────

    async def verify_payment(
        self,
        provider_order_id: str,
        provider_payment_id: str,
        provider_signature: str,
    ) -> bool:
        """
        Verify Razorpay payment signature using HMAC-SHA256.

        Razorpay signature = HMAC-SHA256(
            key    = razorpay_key_secret,
            data   = "{order_id}|{payment_id}"
        )

        This is the ONLY reliable way to confirm a payment.
        Never confirm a booking based on frontend-provided data alone.
        """
        if not self.key_secret:
            logger.error("razorpay_verify_failed_no_secret")
            return False

        try:
            message = f"{provider_order_id}|{provider_payment_id}"
            expected_signature = hmac.new(
                self.key_secret.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            is_valid = hmac.compare_digest(expected_signature, provider_signature)

            if not is_valid:
                logger.warning(
                    "razorpay_signature_mismatch",
                    order_id=provider_order_id,
                    payment_id=provider_payment_id,
                )
            else:
                logger.info(
                    "razorpay_signature_verified",
                    order_id=provider_order_id,
                    payment_id=provider_payment_id,
                )

            return is_valid

        except Exception as e:
            logger.error("razorpay_verify_exception", error=str(e))
            return False

    # ── Payment capture ───────────────────────────────────────────────────────

    async def capture_payment(
        self, provider_payment_id: str, amount: float
    ) -> PaymentCapture:
        """
        Fetch payment details from Razorpay and verify it's captured.
        Called after successful signature verification.
        """
        try:
            client = self._get_client()
            payment = client.payment.fetch(provider_payment_id)
            is_captured = payment.get("status") == "captured"

            if not is_captured:
                logger.warning(
                    "razorpay_payment_not_captured",
                    payment_id=provider_payment_id,
                    status=payment.get("status"),
                )

            return PaymentCapture(
                provider_payment_id=provider_payment_id,
                provider_order_id=payment.get("order_id", ""),
                provider_signature=None,
                captured=is_captured,
                amount=payment.get("amount", 0) / 100,  # Convert paise back to rupees
                provider_data=payment,
            )
        except PaymentError:
            raise
        except Exception as e:
            logger.error("razorpay_capture_failed", payment_id=provider_payment_id, error=str(e))
            raise PaymentError(f"Failed to fetch Razorpay payment: {e}")

    # ── Refunds ───────────────────────────────────────────────────────────────

    async def process_refund(
        self,
        provider_payment_id: str,
        amount: float,
        reason: Optional[str] = None,
    ) -> RefundResult:
        """
        Create a refund via Razorpay.
        Amount is in major units (rupees); converted to paise for Razorpay.
        Partial refunds are supported.
        """
        try:
            client = self._get_client()
            amount_paise = int(round(amount * 100))
            refund_data: dict = {"amount": amount_paise}
            if reason:
                refund_data["notes"] = {"reason": str(reason)[:254]}

            refund = client.payment.refund(provider_payment_id, refund_data)
            logger.info(
                "razorpay_refund_created",
                payment_id=provider_payment_id,
                refund_id=refund["id"],
                amount=amount,
            )
            return RefundResult(
                provider_refund_id=refund["id"],
                status=refund.get("status", "PENDING").upper(),
                amount=refund.get("amount", 0) / 100,
                provider_data=refund,
            )
        except PaymentError:
            raise
        except Exception as e:
            logger.error("razorpay_refund_failed", payment_id=provider_payment_id, error=str(e))
            raise PaymentError(f"Failed to create Razorpay refund: {e}")

    # ── Webhook signature verification ────────────────────────────────────────

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Razorpay webhook signature.

        Razorpay sends: X-Razorpay-Signature header
        Signature = HMAC-SHA256(webhook_secret, raw_request_body)

        Always verify before processing any webhook event.
        Reject requests with invalid signatures immediately.
        """
        if not self.webhook_secret:
            logger.error(
                "razorpay_webhook_secret_not_configured",
                hint="Set RAZORPAY_WEBHOOK_SECRET in environment",
            )
            return False

        try:
            expected = hmac.new(
                self.webhook_secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()
            is_valid = hmac.compare_digest(expected, signature)
            if not is_valid:
                logger.warning("razorpay_webhook_signature_invalid")
            return is_valid
        except Exception as e:
            logger.error("razorpay_webhook_verify_exception", error=str(e))
            return False

    # ── Webhook event processors ──────────────────────────────────────────────

    def parse_webhook_event(self, payload: bytes) -> dict:
        """Parse and return the webhook event payload."""
        try:
            return json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise PaymentError(f"Invalid webhook payload: {e}")

    def get_webhook_event_type(self, event: dict) -> str:
        """Extract event type from parsed webhook payload."""
        return event.get("event", "")

    def get_payment_id_from_webhook(self, event: dict) -> Optional[str]:
        """Extract payment_id from a payment.captured or payment.failed webhook event."""
        try:
            return event["payload"]["payment"]["entity"]["id"]
        except (KeyError, TypeError):
            return None

    def get_order_id_from_webhook(self, event: dict) -> Optional[str]:
        """Extract order_id from a webhook event."""
        try:
            return event["payload"]["payment"]["entity"]["order_id"]
        except (KeyError, TypeError):
            return None

    def get_refund_id_from_webhook(self, event: dict) -> Optional[str]:
        """Extract refund_id from a refund.processed webhook event."""
        try:
            return event["payload"]["refund"]["entity"]["id"]
        except (KeyError, TypeError):
            return None
