"""
PaymentService — complete payment lifecycle with real Razorpay verification.

CRITICAL RULE: Booking confirmation NEVER relies on frontend payment status.
The backend ALWAYS verifies the HMAC signature from Razorpay before confirming.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import assert_business_access
from app.core.exceptions import NotFoundError, PaymentError, TenantIsolationError
from app.core.logging import get_logger
from app.models.appointment import Appointment, AppointmentStatus
from app.models.customer import Customer
from app.models.payment import Invoice, Payment, PaymentProvider, PaymentStatus, Refund
from app.models.user import User
from app.providers.payment.factory import get_payment_provider
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
    RefundRequest,
    VerifyPaymentRequest,
)

logger = get_logger(__name__)


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.provider = get_payment_provider()

    # ── Create order ──────────────────────────────────────────────────────────

    async def create_payment_order(
        self, data: CreatePaymentOrderRequest, user: User
    ) -> PaymentOrderResponse:
        customer = await self._get_customer(user.id)
        appointment = await self._get_appointment(data.appointment_id)

        if str(appointment.customer_id) != str(customer.id):
            raise TenantIsolationError()

        # Idempotent: return existing captured payment
        existing = await self._get_existing_payment(appointment.id)
        if existing and existing.status == PaymentStatus.CAPTURED:
            raise PaymentError("This appointment has already been paid")

        # Create provider order
        order = await self.provider.create_order(
            amount=data.amount,
            currency=data.currency,
            metadata={
                "appointment_id": str(appointment.id),
                "business_id": str(appointment.business_id),
                "customer_id": str(customer.id),
            },
        )

        provider_enum = (
            PaymentProvider.MOCK
            if settings.PAYMENT_PROVIDER.lower() in ("mock", "development")
            else PaymentProvider.RAZORPAY
        )
        payment = Payment(
            business_id=appointment.business_id,
            appointment_id=appointment.id,
            customer_id=customer.id,
            amount=data.amount,
            currency=data.currency,
            provider=provider_enum,
            status=PaymentStatus.PENDING,
            provider_order_id=order.provider_order_id,
        )
        self.db.add(payment)
        await self.db.flush()

        return PaymentOrderResponse(
            payment_id=payment.id,
            provider_order_id=order.provider_order_id,
            amount=data.amount,
            currency=data.currency,
            provider=provider_enum,
            status=PaymentStatus.PENDING,
            provider_key=settings.RAZORPAY_KEY_ID,
        )

    # ── Verify and capture ────────────────────────────────────────────────────

    async def verify_and_capture(
        self, data: VerifyPaymentRequest, user: User
    ) -> Payment:
        """
        Server-side signature verification — the ONLY way to confirm a payment.

        Flow:
          1. Load pending payment record
          2. Verify HMAC-SHA256 signature from Razorpay
          3. If invalid → mark FAILED, raise PaymentError
          4. If valid → mark CAPTURED, confirm appointment, generate invoice
        """
        payment = await self._get_payment(data.payment_id)
        customer = await self._get_customer(user.id)

        if str(payment.customer_id) != str(customer.id):
            raise TenantIsolationError()

        # Idempotent
        if payment.status == PaymentStatus.CAPTURED:
            return payment

        # ── CRITICAL: Server-side signature verification ──────────────────────
        is_valid = await self.provider.verify_payment(
            provider_order_id=data.provider_order_id,
            provider_payment_id=data.provider_payment_id,
            provider_signature=data.provider_signature,
        )

        if not is_valid:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Razorpay signature verification failed — payment rejected"
            self.db.add(payment)
            await self.db.flush()
            logger.warning(
                "payment_signature_verification_failed",
                payment_id=str(payment.id),
                order_id=data.provider_order_id,
                payment_id_provider=data.provider_payment_id,
            )
            raise PaymentError(
                "Payment verification failed. The payment signature is invalid. "
                "If you were charged, please contact support."
            )

        # ── Signature verified — update payment record ────────────────────────
        payment.status = PaymentStatus.CAPTURED
        payment.provider_payment_id = data.provider_payment_id
        payment.provider_signature = data.provider_signature
        payment.paid_at = datetime.now(timezone.utc)
        self.db.add(payment)

        # ── Confirm the appointment ───────────────────────────────────────────
        if payment.appointment_id:
            appointment = await self._get_appointment(payment.appointment_id)
            if appointment.status == AppointmentStatus.PENDING:
                appointment.status = AppointmentStatus.CONFIRMED
                self.db.add(appointment)

        # ── Generate invoice ──────────────────────────────────────────────────
        await self._generate_invoice(payment)

        await self.db.flush()
        logger.info(
            "payment_captured_and_verified",
            payment_id=str(payment.id),
            provider_payment_id=data.provider_payment_id,
        )
        return payment

    # ── Webhook processing ────────────────────────────────────────────────────

    async def process_webhook(self, payload: bytes, signature: str) -> dict:
        """
        Process Razorpay webhook events.

        ALWAYS verify signature first. Reject any webhook with an invalid signature.
        This prevents replay attacks and spoofed webhooks.
        """
        # Step 1: Verify webhook signature
        if not self.provider.verify_webhook_signature(payload, signature):
            logger.warning("webhook_rejected_invalid_signature")
            raise PaymentError("Invalid webhook signature — request rejected")

        # Step 2: Parse event
        try:
            from app.providers.payment.razorpay_provider import RazorpayProvider
            if isinstance(self.provider, RazorpayProvider):
                event = self.provider.parse_webhook_event(payload)
                event_type = self.provider.get_webhook_event_type(event)
            else:
                import json
                event = json.loads(payload.decode())
                event_type = event.get("event", "")
        except Exception as e:
            raise PaymentError(f"Failed to parse webhook: {e}")

        logger.info("webhook_received", event_type=event_type)

        # Step 3: Handle event
        handlers = {
            "payment.captured": self._handle_payment_captured,
            "payment.failed":   self._handle_payment_failed,
            "refund.created":   self._handle_refund_created,
            "refund.processed": self._handle_refund_processed,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(event)
        else:
            logger.info("webhook_event_ignored", event_type=event_type)

        return {"status": "processed", "event": event_type}

    # ── Refunds ───────────────────────────────────────────────────────────────

    async def create_refund(
        self, payment_id: UUID, data: RefundRequest, user: User
    ) -> Refund:
        payment = await self._get_payment(payment_id)
        assert_business_access(user, payment.business_id)

        if payment.status not in [PaymentStatus.CAPTURED, PaymentStatus.PARTIALLY_REFUNDED]:
            raise PaymentError(
                f"Cannot refund a payment in '{payment.status.value}' status. "
                "Only captured payments can be refunded."
            )

        if not payment.provider_payment_id:
            raise PaymentError(
                "No provider payment ID found. Cannot process refund for unconfirmed payment."
            )

        if data.amount > float(payment.amount):
            raise PaymentError(
                f"Refund amount ({data.amount}) exceeds payment amount ({payment.amount})."
            )

        result = await self.provider.process_refund(
            provider_payment_id=payment.provider_payment_id,
            amount=data.amount,
            reason=data.reason,
        )

        refund = Refund(
            payment_id=payment.id,
            business_id=payment.business_id,
            amount=data.amount,
            reason=data.reason,
            provider_refund_id=result.provider_refund_id,
            status=result.status,
            processed_by_id=user.id,
            processed_at=datetime.now(timezone.utc),
        )
        self.db.add(refund)

        payment.status = PaymentStatus.REFUNDED
        self.db.add(payment)
        await self.db.flush()

        logger.info(
            "refund_created",
            payment_id=str(payment.id),
            refund_id=result.provider_refund_id,
            amount=data.amount,
        )
        return refund

    async def get_payment(self, payment_id: UUID, user: User) -> Payment:
        payment = await self._get_payment(payment_id)
        customer = await self._get_customer(user.id)
        if str(payment.customer_id) != str(customer.id):
            assert_business_access(user, payment.business_id)
        return payment

    async def list_business_payments(
        self, business_id: UUID, user: User, offset: int = 0, limit: int = 20
    ) -> List[Payment]:
        assert_business_access(user, business_id)
        result = await self.db.execute(
            select(Payment)
            .where(Payment.business_id == business_id)
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Webhook event handlers ────────────────────────────────────────────────

    async def _handle_payment_captured(self, event: dict) -> None:
        """Handle payment.captured — update payment and confirm appointment."""
        from app.providers.payment.razorpay_provider import RazorpayProvider
        if isinstance(self.provider, RazorpayProvider):
            payment_id = self.provider.get_payment_id_from_webhook(event)
        else:
            payment_id = event.get("payload", {}).get("payment", {}).get("entity", {}).get("id")

        if not payment_id:
            return

        result = await self.db.execute(
            select(Payment).where(Payment.provider_payment_id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment and payment.status != PaymentStatus.CAPTURED:
            payment.status = PaymentStatus.CAPTURED
            payment.paid_at = datetime.now(timezone.utc)
            self.db.add(payment)
            # Also confirm appointment
            if payment.appointment_id:
                appt_result = await self.db.execute(
                    select(Appointment).where(Appointment.id == payment.appointment_id)
                )
                appt = appt_result.scalar_one_or_none()
                if appt and appt.status == AppointmentStatus.PENDING:
                    appt.status = AppointmentStatus.CONFIRMED
                    self.db.add(appt)
            await self.db.flush()
            logger.info("webhook_payment_captured", payment_id=str(payment.id))

    async def _handle_payment_failed(self, event: dict) -> None:
        """Handle payment.failed — mark payment as failed."""
        from app.providers.payment.razorpay_provider import RazorpayProvider
        if isinstance(self.provider, RazorpayProvider):
            order_id = self.provider.get_order_id_from_webhook(event)
        else:
            order_id = (
                event.get("payload", {}).get("payment", {}).get("entity", {}).get("order_id")
            )

        if not order_id:
            return
        result = await self.db.execute(
            select(Payment).where(Payment.provider_order_id == order_id)
        )
        payment = result.scalar_one_or_none()
        if payment and payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Payment failed (webhook event: payment.failed)"
            self.db.add(payment)
            await self.db.flush()
            logger.info("webhook_payment_failed", order_id=order_id)

    async def _handle_refund_created(self, event: dict) -> None:
        logger.info("webhook_refund_created")

    async def _handle_refund_processed(self, event: dict) -> None:
        """Handle refund.processed — update refund status."""
        from app.providers.payment.razorpay_provider import RazorpayProvider
        if isinstance(self.provider, RazorpayProvider):
            refund_id = self.provider.get_refund_id_from_webhook(event)
        else:
            refund_id = (
                event.get("payload", {}).get("refund", {}).get("entity", {}).get("id")
            )

        if not refund_id:
            return
        result = await self.db.execute(
            select(Refund).where(Refund.provider_refund_id == refund_id)
        )
        refund = result.scalar_one_or_none()
        if refund:
            refund.status = "PROCESSED"
            self.db.add(refund)
            await self.db.flush()

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _generate_invoice(self, payment: Payment) -> Invoice:
        import random
        invoice_number = (
            f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
            f"{random.randint(10000, 99999)}"
        )
        invoice = Invoice(
            payment_id=payment.id,
            business_id=payment.business_id,
            customer_id=payment.customer_id,
            invoice_number=invoice_number,
            subtotal=float(payment.amount),
            tax_amount=0.0,
            discount_amount=0.0,
            total_amount=float(payment.amount),
            issued_at=datetime.now(timezone.utc),
        )
        self.db.add(invoice)
        await self.db.flush()
        return invoice

    async def _get_customer(self, user_id: UUID) -> Customer:
        result = await self.db.execute(
            select(Customer).where(Customer.user_id == user_id)
        )
        c = result.scalar_one_or_none()
        if not c:
            raise NotFoundError("Customer", user_id)
        return c

    async def _get_appointment(self, appointment_id: UUID) -> Appointment:
        result = await self.db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        a = result.scalar_one_or_none()
        if not a:
            raise NotFoundError("Appointment", appointment_id)
        return a

    async def _get_payment(self, payment_id: UUID) -> Payment:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        p = result.scalar_one_or_none()
        if not p:
            raise NotFoundError("Payment", payment_id)
        return p

    async def _get_existing_payment(self, appointment_id: UUID) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(
                Payment.appointment_id == appointment_id,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.CAPTURED]),
            )
        )
        return result.scalar_one_or_none()
