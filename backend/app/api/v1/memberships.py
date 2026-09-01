"""
Memberships API Endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.membership import (
    CustomerMembershipCreate,
    CustomerMembershipResponse,
    MembershipPlanCreate,
    MembershipPlanResponse,
    MembershipPlanUpdate,
)
from app.services.membership_service import MembershipService

router = APIRouter(prefix="/businesses/{business_id}/memberships", tags=["memberships"])


def get_membership_service(db: AsyncSession = Depends(get_db)) -> MembershipService:
    return MembershipService(db)


# ── Plans ────────────────────────────────────────────────────────────────────

@router.get("/plans", response_model=List[MembershipPlanResponse])
async def list_membership_plans(
    business_id: UUID,
    is_active: Optional[bool] = None,
    svc: MembershipService = Depends(get_membership_service),
):
    """List salon membership plans/tiers."""
    return await svc.list_plans(business_id, is_active)


@router.post("/plans", response_model=MembershipPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_membership_plan(
    business_id: UUID,
    data: MembershipPlanCreate,
    user: CurrentUser,
    svc: MembershipService = Depends(get_membership_service),
):
    """Create a new membership plan tier."""
    return await svc.create_plan(business_id, data, user)


@router.patch("/plans/{plan_id}", response_model=MembershipPlanResponse)
async def update_membership_plan(
    business_id: UUID,
    plan_id: UUID,
    data: MembershipPlanUpdate,
    user: CurrentUser,
    svc: MembershipService = Depends(get_membership_service),
):
    """Update a membership plan tier."""
    return await svc.update_plan(plan_id, business_id, data, user)


# ── Customer Subscriptions ───────────────────────────────────────────────────

@router.post("/enroll", response_model=CustomerMembershipResponse, status_code=status.HTTP_201_CREATED)
async def enroll_customer(
    business_id: UUID,
    data: CustomerMembershipCreate,
    user: CurrentUser,
    svc: MembershipService = Depends(get_membership_service),
):
    """Enroll a customer into a membership plan."""
    return await svc.enroll_customer(business_id, data, user)


@router.get("/customers", response_model=List[CustomerMembershipResponse])
async def list_customer_memberships(
    business_id: UUID,
    customer_id: Optional[UUID] = None,
    svc: MembershipService = Depends(get_membership_service),
):
    """List active and historical customer memberships."""
    return await svc.list_customer_memberships(business_id, customer_id)
