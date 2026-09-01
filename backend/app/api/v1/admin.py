"""
Platform admin endpoints.
All routes require PLATFORM_ADMIN role.
All actions are audit-logged.
"""
import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_platform_admin
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.audit import AuditLog
from app.models.business import Business, BusinessStatus
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import SubscriptionPlan
from app.models.user import User
from app.schemas.admin import (
    AdminBusinessUpdate,
    AdminUserUpdate,
    DashboardStats,
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
)
from app.schemas.business import BusinessResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.payment import PaymentResponse
from app.schemas.user import UserResponse

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_platform_admin())],
)


async def _audit(
    db: AsyncSession,
    actor_id: UUID,
    action: str,
    entity_type: str,
    entity_id: str,
    new_values: Optional[dict] = None,
) -> None:
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        new_values=json.dumps(new_values) if new_values else None,
    )
    db.add(log)
    await db.flush()


# ── Dashboard ─────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_businesses = (await db.execute(
        select(func.count(Business.id)).where(Business.deleted_at.is_(None))
    )).scalar_one()

    active_businesses = (await db.execute(
        select(func.count(Business.id)).where(
            Business.status == BusinessStatus.ACTIVE, Business.deleted_at.is_(None)
        )
    )).scalar_one()

    total_users = (await db.execute(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )).scalar_one()

    total_bookings = (await db.execute(
        select(func.count(Appointment.id)).where(Appointment.deleted_at.is_(None))
    )).scalar_one()

    revenue_result = (await db.execute(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.CAPTURED)
    )).scalar_one()
    total_revenue = float(revenue_result or 0)

    bookings_today = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.start_time >= today_start,
            Appointment.deleted_at.is_(None),
        )
    )).scalar_one()

    new_businesses = (await db.execute(
        select(func.count(Business.id)).where(
            Business.created_at >= month_start, Business.deleted_at.is_(None)
        )
    )).scalar_one()

    new_users = (await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= month_start, User.deleted_at.is_(None)
        )
    )).scalar_one()

    return DashboardStats(
        total_businesses=total_businesses,
        active_businesses=active_businesses,
        total_users=total_users,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        bookings_today=bookings_today,
        new_businesses_this_month=new_businesses,
        new_users_this_month=new_users,
    )


# ── Businesses ─────────────────────────────────────────────────────────────────


@router.get("/businesses", response_model=PaginatedResponse[BusinessResponse])
async def list_businesses(
    q: Optional[str] = Query(default=None),
    status_filter: Optional[BusinessStatus] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    query = select(Business).where(Business.deleted_at.is_(None))
    count_q = select(func.count(Business.id)).where(Business.deleted_at.is_(None))

    if q:
        like = f"%{q}%"
        query = query.where(Business.name.ilike(like))
        count_q = count_q.where(Business.name.ilike(like))
    if status_filter:
        query = query.where(Business.status == status_filter)
        count_q = count_q.where(Business.status == status_filter)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(query.offset(offset).limit(page_size))
    businesses = list(result.scalars().all())
    return PaginatedResponse.create(businesses, total, page, page_size)


@router.patch("/businesses/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: UUID,
    data: AdminBusinessUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Business not found")

    update = data.model_dump(exclude_unset=True)
    for k, v in update.items():
        setattr(business, k, v)
    db.add(business)

    await _audit(db, current_user.id, "admin.business.update", "business",
                 str(business_id), update)
    return business


# ── Users ──────────────────────────────────────────────────────────────────────


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    q: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    query = select(User).where(User.deleted_at.is_(None))
    count_q = select(func.count(User.id)).where(User.deleted_at.is_(None))

    if q:
        like = f"%{q}%"
        query = query.where(
            User.email.ilike(like) | User.first_name.ilike(like) | User.last_name.ilike(like)
        )
        count_q = count_q.where(
            User.email.ilike(like) | User.first_name.ilike(like) | User.last_name.ilike(like)
        )

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(query.offset(offset).limit(page_size))
    users = list(result.scalars().all())
    return PaginatedResponse.create(users, total, page, page_size)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: AdminUserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    update = data.model_dump(exclude_unset=True)
    for k, v in update.items():
        setattr(user, k, v)
    db.add(user)

    await _audit(db, current_user.id, "admin.user.update", "user", str(user_id), update)
    return user


# ── Bookings ───────────────────────────────────────────────────────────────────


@router.get("/bookings", response_model=PaginatedResponse[dict])
async def list_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    total = (await db.execute(
        select(func.count(Appointment.id)).where(Appointment.deleted_at.is_(None))
    )).scalar_one()
    result = await db.execute(
        select(Appointment)
        .where(Appointment.deleted_at.is_(None))
        .order_by(Appointment.created_at.desc())
        .offset(offset).limit(page_size)
    )
    appointments = result.scalars().all()
    items = [
        {
            "id": str(a.id),
            "business_id": str(a.business_id),
            "status": a.status.value,
            "start_time": a.start_time.isoformat(),
            "total_amount": float(a.total_amount),
            "created_at": a.created_at.isoformat(),
        }
        for a in appointments
    ]
    return PaginatedResponse.create(items, total, page, page_size)


# ── Payments ───────────────────────────────────────────────────────────────────


@router.get("/payments", response_model=PaginatedResponse[PaymentResponse])
async def list_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    total = (await db.execute(select(func.count(Payment.id)))).scalar_one()
    result = await db.execute(
        select(Payment).order_by(Payment.created_at.desc()).offset(offset).limit(page_size)
    )
    payments = list(result.scalars().all())
    return PaginatedResponse.create(payments, total, page, page_size)


# ── Subscription Plans ─────────────────────────────────────────────────────────


@router.get("/subscription-plans", response_model=List[SubscriptionPlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True)))
    return list(result.scalars().all())


@router.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=201)
async def create_plan(
    data: SubscriptionPlanCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    plan = SubscriptionPlan(**data.model_dump())
    db.add(plan)
    await db.flush()
    await _audit(db, current_user.id, "admin.plan.create", "subscription_plan",
                 str(plan.id), data.model_dump())
    return plan


# ── Audit Logs ─────────────────────────────────────────────────────────────────


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    total = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    )
    logs = result.scalars().all()
    items = [
        {
            "id": str(log.id),
            "actor_id": str(log.actor_id) if log.actor_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
    return PaginatedResponse.create(items, total, page, page_size)
