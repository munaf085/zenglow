"""
Subscription Service — plans, Razorpay checkout order generation, HMAC verification, and plan upgrades.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import assert_business_access
from app.core.exceptions import BusinessRuleError, NotFoundError, PaymentError
from app.core.logging import get_logger
from app.models.business import Business
from app.models.subscription import (
    BillingCycle,
    PlanTier,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from app.models.user import User
from app.providers.payment.factory import get_payment_provider
from app.schemas.subscription import (
    CreateSubscriptionOrderRequest,
    SubscriptionDetailsResponse,
    SubscriptionOrderResponse,
    VerifySubscriptionRequest,
)

logger = get_logger(__name__)


# Default SaaS subscription tiers
DEFAULT_PLANS = [
    {
        "tier": PlanTier.STARTER,
        "name": "Starter Plan",
        "description": "Perfect for single salons or barbershops getting started with digital booking.",
        "monthly_price": 999.0,
        "yearly_price": 9990.0,  # ~2 months free
        "max_branches": 1,
        "max_staff": 5,
        "max_services": 25,
        "max_bookings_per_month": 300,
        "is_active": True,
    },
    {
        "tier": PlanTier.PROFESSIONAL,
        "name": "Professional Plan",
        "description": "For growing salons and spas with multiple staff, inventory, and POS checkout.",
        "monthly_price": 2499.0,
        "yearly_price": 24990.0,
        "max_branches": 2,
        "max_staff": 15,
        "max_services": 100,
        "max_bookings_per_month": 1500,
        "is_active": True,
    },
    {
        "tier": PlanTier.ENTERPRISE,
        "name": "Enterprise Plan",
        "description": "For multi-branch beauty chains, luxury wellness resorts, and franchise salons.",
        "monthly_price": 4999.0,
        "yearly_price": 49990.0,
        "max_branches": 10,
        "max_staff": 100,
        "max_services": 500,
        "max_bookings_per_month": 10000,
        "is_active": True,
    },
]


class SubscriptionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.provider = get_payment_provider()

    async def list_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        """List subscription plans, auto-seeding default tiers if empty."""
        q = select(SubscriptionPlan)
        if active_only:
            q = q.where(SubscriptionPlan.is_active.is_(True))
        q = q.order_by(SubscriptionPlan.monthly_price)

        result = await self.db.execute(q)
        plans = list(result.scalars().all())

        if not plans:
            # Seed defaults
            for p_data in DEFAULT_PLANS:
                p = SubscriptionPlan(**p_data)
                self.db.add(p)
            await self.db.flush()

            result = await self.db.execute(q)
            plans = list(result.scalars().all())

        return plans

    async def get_plan(self, plan_id: UUID) -> SubscriptionPlan:
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundError("SubscriptionPlan", plan_id)
        return plan

    async def create_subscription_order(
        self, data: CreateSubscriptionOrderRequest, user: User
    ) -> SubscriptionOrderResponse:
        """Create a Razorpay order to initiate subscription checkout."""
        assert_business_access(user, data.business_id)
        plan = await self.get_plan(data.plan_id)

        # Calculate price based on billing cycle
        price = (
            float(plan.yearly_price)
            if data.billing_cycle == BillingCycle.YEARLY
            else float(plan.monthly_price)
        )

        # Create provider payment order
        order_meta = {
            "business_id": str(data.business_id),
            "plan_id": str(plan.id),
            "billing_cycle": data.billing_cycle.value,
            "type": "SUBSCRIPTION",
        }

        order = await self.provider.create_order(
            amount=price,
            currency=plan.currency or "INR",
            metadata=order_meta,
        )

        return SubscriptionOrderResponse(
            provider_order_id=order.provider_order_id,
            amount=price,
            currency=plan.currency or "INR",
            key_id=settings.RAZORPAY_KEY_ID or "rzp_test_mock",
            business_id=data.business_id,
            plan_id=plan.id,
            billing_cycle=data.billing_cycle,
            plan_name=plan.name,
        )

    async def verify_and_activate_subscription(
        self, data: VerifySubscriptionRequest, user: User
    ) -> SubscriptionDetailsResponse:
        """
        Verify payment signature and activate business subscription.
        NEVER trust frontend payment status — always verify signature on the server side.
        """
        assert_business_access(user, data.business_id)
        plan = await self.get_plan(data.plan_id)

        # 1. Verify HMAC Signature
        valid = await self.provider.verify_payment(
            provider_order_id=data.provider_order_id,
            provider_payment_id=data.provider_payment_id,
            provider_signature=data.provider_signature,
        )
        if not valid:
            logger.error(
                "Subscription payment signature verification failed",
                order_id=data.provider_order_id,
                payment_id=data.provider_payment_id,
            )
            raise PaymentError("Invalid payment signature from provider")

        # 2. Update Business Plan
        biz_res = await self.db.execute(
            select(Business).where(Business.id == data.business_id)
        )
        business = biz_res.scalar_one_or_none()
        if not business:
            raise NotFoundError("Business", data.business_id)

        business.subscription_plan_id = plan.id
        self.db.add(business)

        # 3. Create or Update Subscription record
        now = datetime.now(timezone.utc)
        duration_days = 365 if data.billing_cycle == BillingCycle.YEARLY else 30
        end_date = now + timedelta(days=duration_days)

        subscription = Subscription(
            business_id=business.id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=data.billing_cycle,
            start_date=now,
            end_date=end_date,
        )
        self.db.add(subscription)
        await self.db.flush()
        await self.db.refresh(subscription, ["plan"])

        logger.info(
            f"Business '{business.name}' upgraded to {plan.tier.value} plan ({data.billing_cycle.value})",
            business_id=str(business.id),
            plan_id=str(plan.id),
        )

        return SubscriptionDetailsResponse.model_validate(subscription)

    async def get_current_subscription(
        self, business_id: UUID, user: User
    ) -> Optional[SubscriptionDetailsResponse]:
        """Get the current active subscription for a business."""
        assert_business_access(user, business_id)
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.business_id == business_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .order_by(Subscription.end_date.desc())
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return None
        return SubscriptionDetailsResponse.model_validate(sub)
