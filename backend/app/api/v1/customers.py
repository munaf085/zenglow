"""
Customer CRM endpoints — customer profiles and business-side customer management.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, assert_business_access
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.customer import Customer
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(tags=["customers"])


# ── Public customer profile schemas ──────────────────────────────────────────


class CustomerProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    notes: Optional[str] = None
    tags: Optional[str] = None
    marketing_opt_in: bool
    sms_opt_in: bool

    # Joined from User
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerUpdateRequest(BaseModel):
    notes: Optional[str] = None
    tags: Optional[str] = None
    marketing_opt_in: Optional[bool] = None
    sms_opt_in: Optional[bool] = None


# ── My profile ────────────────────────────────────────────────────────────────


@router.get("/customers/me", response_model=CustomerProfileResponse)
async def get_my_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get the current customer's profile."""
    result = await db.execute(
        select(Customer).where(Customer.user_id == current_user.id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer profile")

    resp = CustomerProfileResponse(
        id=customer.id,
        user_id=customer.user_id,
        notes=customer.notes,
        tags=customer.tags,
        marketing_opt_in=customer.marketing_opt_in,
        sms_opt_in=customer.sms_opt_in,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        created_at=customer.created_at,
    )
    return resp


@router.patch("/customers/me", response_model=CustomerProfileResponse)
async def update_my_profile(
    data: CustomerUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Customer).where(Customer.user_id == current_user.id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer profile")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(customer, k, v)
    db.add(customer)
    await db.flush()

    return CustomerProfileResponse(
        id=customer.id,
        user_id=customer.user_id,
        notes=customer.notes,
        tags=customer.tags,
        marketing_opt_in=customer.marketing_opt_in,
        sms_opt_in=customer.sms_opt_in,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        created_at=customer.created_at,
    )


# ── Business-side CRM ─────────────────────────────────────────────────────────


@router.get(
    "/businesses/{business_id}/customers",
    response_model=PaginatedResponse[CustomerProfileResponse],
)
async def list_business_customers(
    business_id: UUID,
    q: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """List customers who have booked with this business."""
    assert_business_access(current_user, business_id)

    from app.models.appointment import Appointment
    from sqlalchemy import func, distinct

    # Find unique customer IDs via appointments
    offset = (page - 1) * page_size

    count_q = (
        select(func.count(distinct(Appointment.customer_id)))
        .where(Appointment.business_id == business_id)
    )
    total = (await db.execute(count_q)).scalar_one()

    cust_ids_q = (
        select(distinct(Appointment.customer_id))
        .where(Appointment.business_id == business_id)
        .offset(offset)
        .limit(page_size)
    )
    cust_id_rows = (await db.execute(cust_ids_q)).scalars().all()

    items = []
    for cid in cust_id_rows:
        c_result = await db.execute(
            select(Customer).where(Customer.id == cid)
        )
        customer = c_result.scalar_one_or_none()
        if not customer:
            continue
        u_result = await db.execute(select(User).where(User.id == customer.user_id))
        user = u_result.scalar_one_or_none()
        if not user:
            continue
        # Filter by name/email search
        if q:
            q_lower = q.lower()
            if not (
                q_lower in user.email.lower()
                or q_lower in user.first_name.lower()
                or q_lower in user.last_name.lower()
            ):
                continue
        items.append(
            CustomerProfileResponse(
                id=customer.id,
                user_id=customer.user_id,
                notes=customer.notes,
                tags=customer.tags,
                marketing_opt_in=customer.marketing_opt_in,
                sms_opt_in=customer.sms_opt_in,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                created_at=customer.created_at,
            )
        )

    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/businesses/{business_id}/customers/{customer_id}",
    response_model=CustomerProfileResponse,
)
async def get_business_customer(
    business_id: UUID,
    customer_id: UUID,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    assert_business_access(current_user, business_id)

    # Verify this customer has appointments with this business
    from app.models.appointment import Appointment
    from sqlalchemy import exists

    has_appt = (await db.execute(
        select(exists().where(
            Appointment.customer_id == customer_id,
            Appointment.business_id == business_id,
        ))
    )).scalar()

    if not has_appt:
        raise NotFoundError("Customer", customer_id)

    c_result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = c_result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer", customer_id)

    u_result = await db.execute(select(User).where(User.id == customer.user_id))
    user = u_result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User")

    return CustomerProfileResponse(
        id=customer.id,
        user_id=customer.user_id,
        notes=customer.notes,
        tags=customer.tags,
        marketing_opt_in=customer.marketing_opt_in,
        sms_opt_in=customer.sms_opt_in,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        created_at=customer.created_at,
    )


@router.patch(
    "/businesses/{business_id}/customers/{customer_id}",
    response_model=CustomerProfileResponse,
)
async def update_business_customer(
    business_id: UUID,
    customer_id: UUID,
    data: CustomerUpdateRequest,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Business staff can update CRM notes/tags for a customer."""
    assert_business_access(current_user, business_id)

    c_result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = c_result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer", customer_id)

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(customer, k, v)
    db.add(customer)
    await db.flush()

    u_result = await db.execute(select(User).where(User.id == customer.user_id))
    user = u_result.scalar_one()

    return CustomerProfileResponse(
        id=customer.id,
        user_id=customer.user_id,
        notes=customer.notes,
        tags=customer.tags,
        marketing_opt_in=customer.marketing_opt_in,
        sms_opt_in=customer.sms_opt_in,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        created_at=customer.created_at,
    )
