"""
Payment endpoints.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
    VerifyPaymentRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


def _svc(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.post("/orders", response_model=PaymentOrderResponse, status_code=201)
async def create_order(
    data: CreatePaymentOrderRequest,
    current_user: CurrentUser,
    svc: PaymentService = Depends(_svc),
):
    """Create a payment order to initiate checkout."""
    return await svc.create_payment_order(data, current_user)


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    data: VerifyPaymentRequest,
    current_user: CurrentUser,
    svc: PaymentService = Depends(_svc),
):
    """
    Verify payment on the server side.
    NEVER trust frontend payment status — always verify here.
    """
    payment = await svc.verify_and_capture(data, current_user)
    return payment


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    svc: PaymentService = Depends(_svc),
):
    """Receive payment provider webhooks."""
    payload = await request.body()
    result = await svc.process_webhook(payload, x_razorpay_signature or "")
    return result


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    current_user: CurrentUser,
    svc: PaymentService = Depends(_svc),
):
    return await svc.get_payment(payment_id, current_user)


@router.get("/businesses/{business_id}/payments", response_model=List[PaymentResponse])
async def list_business_payments(
    business_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = None,
    svc: PaymentService = Depends(_svc),
):
    offset = (page - 1) * page_size
    return await svc.list_business_payments(business_id, current_user, offset, page_size)


@router.post("/{payment_id}/refunds", response_model=RefundResponse, status_code=201)
async def create_refund(
    payment_id: UUID,
    data: RefundRequest,
    current_user: CurrentUser,
    svc: PaymentService = Depends(_svc),
):
    return await svc.create_refund(payment_id, data, current_user)
