"""
Subscriptions API Endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.subscription import (
    CreateSubscriptionOrderRequest,
    SubscriptionDetailsResponse,
    SubscriptionOrderResponse,
    SubscriptionPlanResponse,
    VerifySubscriptionRequest,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_plans(
    active_only: bool = Query(True),
    svc: SubscriptionService = Depends(get_subscription_service),
):
    """List available SaaS subscription plan tiers."""
    plans = await svc.list_plans(active_only=active_only)
    return [SubscriptionPlanResponse.model_validate(p) for p in plans]


@router.post("/create-order", response_model=SubscriptionOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription_order(
    data: CreateSubscriptionOrderRequest,
    user: CurrentUser,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    """Initiate a Razorpay payment order for upgrading business subscription."""
    return await svc.create_subscription_order(data, user)


@router.post("/verify", response_model=SubscriptionDetailsResponse)
async def verify_subscription(
    data: VerifySubscriptionRequest,
    user: CurrentUser,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    """Verify Razorpay payment HMAC signature and activate business plan."""
    return await svc.verify_and_activate_subscription(data, user)


@router.get("/businesses/{business_id}/current", response_model=Optional[SubscriptionDetailsResponse])
async def get_current_subscription(
    business_id: UUID,
    user: CurrentUser,
    svc: SubscriptionService = Depends(get_subscription_service),
):
    """Get active subscription details for a business."""
    return await svc.get_current_subscription(business_id, user)
