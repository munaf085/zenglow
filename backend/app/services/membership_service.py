"""
Membership Service — plans, customer enrollments, and benefit checks.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import assert_business_access
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.membership import CustomerMembership, MembershipPlan, MembershipStatus
from app.models.user import User
from app.schemas.membership import (
    CustomerMembershipCreate,
    MembershipPlanCreate,
    MembershipPlanUpdate,
)


class MembershipService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Membership Plans ─────────────────────────────────────────────────────

    async def list_plans(
        self, business_id: UUID, is_active: Optional[bool] = None
    ) -> List[MembershipPlan]:
        q = select(MembershipPlan).where(
            MembershipPlan.business_id == business_id,
            MembershipPlan.deleted_at.is_(None),
        )
        if is_active is not None:
            q = q.where(MembershipPlan.is_active == is_active)
        q = q.order_by(MembershipPlan.price)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_plan(self, plan_id: UUID, business_id: UUID) -> MembershipPlan:
        result = await self.db.execute(
            select(MembershipPlan).where(
                MembershipPlan.id == plan_id,
                MembershipPlan.business_id == business_id,
                MembershipPlan.deleted_at.is_(None),
            )
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise NotFoundError("MembershipPlan", plan_id)
        return plan

    async def create_plan(
        self, business_id: UUID, data: MembershipPlanCreate, user: User
    ) -> MembershipPlan:
        assert_business_access(user, business_id)

        plan = MembershipPlan(
            business_id=business_id,
            name=data.name.strip(),
            description=data.description,
            price=data.price,
            duration_months=data.duration_months,
            discount_percentage=data.discount_percentage,
            free_services_count=data.free_services_count,
            is_active=data.is_active,
        )
        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def update_plan(
        self, plan_id: UUID, business_id: UUID, data: MembershipPlanUpdate, user: User
    ) -> MembershipPlan:
        assert_business_access(user, business_id)
        plan = await self.get_plan(plan_id, business_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(plan, key, value)

        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    # ── Customer Memberships ─────────────────────────────────────────────────

    async def enroll_customer(
        self, business_id: UUID, data: CustomerMembershipCreate, user: User
    ) -> CustomerMembership:
        assert_business_access(user, business_id)
        plan = await self.get_plan(data.plan_id, business_id)

        now = datetime.now(timezone.utc)
        # Approximate months as 30 days per month
        end_date = now + timedelta(days=plan.duration_months * 30)

        resolved_cust_id = await self._resolve_customer_id(data.customer_id)

        membership = CustomerMembership(
            business_id=business_id,
            customer_id=resolved_cust_id,
            plan_id=plan.id,
            status=MembershipStatus.ACTIVE,
            start_date=now,
            end_date=end_date,
            free_services_remaining=plan.free_services_count,
            notes=data.notes,
        )
        self.db.add(membership)
        await self.db.flush()
        await self.db.refresh(membership, ["plan"])
        return membership

    async def list_customer_memberships(
        self, business_id: UUID, customer_id: Optional[UUID] = None
    ) -> List[CustomerMembership]:
        q = (
            select(CustomerMembership)
            .options(selectinload(CustomerMembership.plan))
            .where(
                CustomerMembership.business_id == business_id,
                CustomerMembership.deleted_at.is_(None),
            )
        )
        if customer_id:
            resolved_id = await self._resolve_customer_id(customer_id)
            q = q.where(CustomerMembership.customer_id == resolved_id)
        q = q.order_by(CustomerMembership.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def _resolve_customer_id(self, id_val: Optional[UUID]) -> Optional[UUID]:
        if not id_val:
            return None
        from app.models.customer import Customer
        from sqlalchemy import or_
        res = await self.db.execute(
            select(Customer.id).where(
                or_(Customer.id == id_val, Customer.user_id == id_val)
            )
        )
        found_id = res.scalar_one_or_none()
        return found_id or id_val

    async def get_active_membership_for_customer(
        self, business_id: UUID, customer_id: UUID
    ) -> Optional[CustomerMembership]:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(CustomerMembership)
            .options(selectinload(CustomerMembership.plan))
            .where(
                CustomerMembership.business_id == business_id,
                CustomerMembership.customer_id == customer_id,
                CustomerMembership.status == MembershipStatus.ACTIVE,
                CustomerMembership.end_date >= now,
                CustomerMembership.deleted_at.is_(None),
            )
            .order_by(CustomerMembership.end_date.desc())
        )
        return result.scalar_one_or_none()
