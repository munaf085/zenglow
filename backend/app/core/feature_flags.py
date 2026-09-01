"""
Feature flags gated by subscription plan tier.

Every module access is checked against the business's active subscription plan.
Plans define hard limits (max_branches, max_staff, etc.) and feature toggles.

Usage in a route:
    from app.core.feature_flags import require_feature, Feature
    await require_feature(Feature.MULTI_BRANCH, business_id, db)

Usage as a FastAPI dependency:
    Depends(feature_guard(Feature.INVENTORY))
"""
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.business import Business
from app.models.subscription import PlanTier, Subscription, SubscriptionPlan, SubscriptionStatus

logger = get_logger(__name__)


class Feature(str, Enum):
    """
    All gated features. Assigned to plan tiers below.
    Free tier gets the core booking engine only.
    """
    # ── Core (all plans) ──────────────────────────────────────────────────────
    ONLINE_BOOKING    = "ONLINE_BOOKING"
    STAFF_MANAGEMENT  = "STAFF_MANAGEMENT"
    SERVICE_CATALOG   = "SERVICE_CATALOG"
    CALENDAR          = "CALENDAR"
    CUSTOMER_CRM      = "CUSTOMER_CRM"
    BASIC_REPORTS     = "BASIC_REPORTS"
    NOTIFICATIONS     = "NOTIFICATIONS"

    # ── Starter + ─────────────────────────────────────────────────────────────
    PAYMENTS_ONLINE   = "PAYMENTS_ONLINE"
    REVIEWS           = "REVIEWS"
    DEPOSITS          = "DEPOSITS"
    CANCELLATION_FEE  = "CANCELLATION_FEE"

    # ── Professional + ────────────────────────────────────────────────────────
    MULTI_BRANCH      = "MULTI_BRANCH"
    ADVANCED_REPORTS  = "ADVANCED_REPORTS"
    PACKAGES          = "PACKAGES"
    MEMBERSHIPS       = "MEMBERSHIPS"
    GIFT_CARDS        = "GIFT_CARDS"
    WAITLIST          = "WAITLIST"
    RESOURCE_MGMT     = "RESOURCE_MGMT"
    MARKETING_BASIC   = "MARKETING_BASIC"

    # ── Enterprise ────────────────────────────────────────────────────────────
    INVENTORY         = "INVENTORY"
    LOYALTY           = "LOYALTY"
    MARKETING_ADVANCED= "MARKETING_ADVANCED"
    STAFF_COMMISSIONS = "STAFF_COMMISSIONS"
    API_ACCESS        = "API_ACCESS"
    WHITELABEL        = "WHITELABEL"
    MULTI_LOCATION    = "MULTI_LOCATION"   # consolidated cross-branch view
    ADVANCED_ANALYTICS= "ADVANCED_ANALYTICS"


# Plan → Feature mapping (cumulative — higher tiers include lower tier features)
PLAN_FEATURES: dict[str, set[Feature]] = {
    PlanTier.FREE.value: {
        Feature.ONLINE_BOOKING,
        Feature.STAFF_MANAGEMENT,
        Feature.SERVICE_CATALOG,
        Feature.CALENDAR,
        Feature.CUSTOMER_CRM,
        Feature.BASIC_REPORTS,
        Feature.NOTIFICATIONS,
    },
    PlanTier.STARTER.value: {
        # All FREE features +
        Feature.PAYMENTS_ONLINE,
        Feature.REVIEWS,
        Feature.DEPOSITS,
        Feature.CANCELLATION_FEE,
    },
    PlanTier.PROFESSIONAL.value: {
        # All STARTER features +
        Feature.MULTI_BRANCH,
        Feature.ADVANCED_REPORTS,
        Feature.PACKAGES,
        Feature.MEMBERSHIPS,
        Feature.GIFT_CARDS,
        Feature.WAITLIST,
        Feature.RESOURCE_MGMT,
        Feature.MARKETING_BASIC,
    },
    PlanTier.ENTERPRISE.value: {
        # All PROFESSIONAL features +
        Feature.INVENTORY,
        Feature.LOYALTY,
        Feature.MARKETING_ADVANCED,
        Feature.STAFF_COMMISSIONS,
        Feature.API_ACCESS,
        Feature.WHITELABEL,
        Feature.MULTI_LOCATION,
        Feature.ADVANCED_ANALYTICS,
    },
}

# Tier ordering for cumulative resolution
_TIER_ORDER = [
    PlanTier.FREE.value,
    PlanTier.STARTER.value,
    PlanTier.PROFESSIONAL.value,
    PlanTier.ENTERPRISE.value,
]


def get_features_for_tier(tier: str) -> set[Feature]:
    """Return the full cumulative feature set for a given plan tier."""
    features: set[Feature] = set()
    for t in _TIER_ORDER:
        features |= PLAN_FEATURES.get(t, set())
        if t == tier:
            break
    return features


async def get_business_tier(business_id: UUID, db: AsyncSession) -> str:
    """
    Resolve the current active subscription tier for a business.
    Falls back to FREE if no active subscription.
    """
    result = await db.execute(
        select(SubscriptionPlan.tier)
        .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
        .where(
            Subscription.business_id == business_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    tier = result.scalar_one_or_none()
    return tier or PlanTier.FREE.value


async def has_feature(
    feature: Feature, business_id: UUID, db: AsyncSession
) -> bool:
    """Check if a business has access to a specific feature."""
    tier = await get_business_tier(business_id, db)
    return feature in get_features_for_tier(tier)


async def require_feature(
    feature: Feature, business_id: UUID, db: AsyncSession
) -> None:
    """
    Raise HTTP 402 (Payment Required) if the business does not have
    access to the requested feature under their current plan.
    """
    if not await has_feature(feature, business_id, db):
        tier = await get_business_tier(business_id, db)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "FEATURE_NOT_AVAILABLE",
                "message": f"The '{feature}' feature is not available on your current plan ({tier}). Please upgrade.",
                "current_tier": tier,
                "required_feature": feature,
            },
        )


async def check_staff_limit(business_id: UUID, current_count: int, db: AsyncSession) -> None:
    """Raise if adding a staff member would exceed the plan limit."""
    result = await db.execute(
        select(SubscriptionPlan.max_staff)
        .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
        .where(
            Subscription.business_id == business_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    max_staff = result.scalar_one_or_none() or 2  # FREE default
    if current_count >= max_staff:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "PLAN_LIMIT_REACHED",
                "message": f"Your plan allows a maximum of {max_staff} staff members. Please upgrade to add more.",
                "limit": max_staff,
                "current": current_count,
            },
        )


async def check_branch_limit(business_id: UUID, current_count: int, db: AsyncSession) -> None:
    """Raise if adding a branch would exceed the plan limit."""
    result = await db.execute(
        select(SubscriptionPlan.max_branches)
        .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
        .where(
            Subscription.business_id == business_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    max_branches = result.scalar_one_or_none() or 1  # FREE default
    if current_count >= max_branches:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "PLAN_LIMIT_REACHED",
                "message": f"Your plan allows a maximum of {max_branches} branch(es). Please upgrade.",
                "limit": max_branches,
                "current": current_count,
            },
        )


def feature_guard(feature: Feature):
    """
    FastAPI dependency factory for feature gating.

    Usage:
        @router.post("/inventory", dependencies=[Depends(feature_guard(Feature.INVENTORY))])
    """
    async def _check(
        business_id: UUID,
        db: AsyncSession = Depends(get_db),
    ) -> None:
        await require_feature(feature, business_id, db)
    return _check
