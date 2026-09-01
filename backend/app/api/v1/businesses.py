"""
Business and Branch API endpoints.
"""
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.redis import get_redis
from app.db.session import get_db
from app.schemas.business import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
    BusinessCreate,
    BusinessResponse,
    BusinessUpdate,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.staff import WorkingHoursResponse, WorkingHoursSetRequest
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.staff_service import StaffService

router = APIRouter(prefix="/businesses", tags=["businesses"])


def _svc(db: AsyncSession = Depends(get_db)) -> BusinessService:
    return BusinessService(db)


def _auth(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> AuthService:
    return AuthService(db, redis)


# ── Business CRUD ─────────────────────────────────────────────────────────────


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    data: BusinessCreate,
    current_user: CurrentUser,
    svc: BusinessService = Depends(_svc),
    auth_svc: AuthService = Depends(_auth),
):
    business = await svc.create_business(current_user, data, auth_svc)
    return business


@router.get("", response_model=PaginatedResponse[BusinessResponse])
async def list_my_businesses(
    current_user: CurrentUser,
    svc: BusinessService = Depends(_svc),
):
    businesses = await svc.list_my_businesses(current_user)
    return PaginatedResponse.create(businesses, len(businesses), 1, len(businesses) or 1)


@router.get("/search", response_model=PaginatedResponse[BusinessResponse])
async def search_businesses(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    svc: BusinessService = Depends(_svc),
):
    offset = (page - 1) * page_size
    businesses, total = await svc.search_businesses(
        query=q, category=category, city=city, offset=offset, limit=page_size
    )
    return PaginatedResponse.create(businesses, total, page, page_size)


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: UUID,
    current_user: CurrentUser,
    svc: BusinessService = Depends(_svc),
):
    return await svc.get_business(business_id, current_user)


@router.get("/public/{slug}", response_model=BusinessResponse)
async def get_public_business(
    slug: str,
    svc: BusinessService = Depends(_svc),
):
    """Public endpoint — no auth required."""
    return await svc.get_public_business(slug)


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: UUID,
    data: BusinessUpdate,
    current_user: CurrentUser,
    svc: BusinessService = Depends(_svc),
):
    return await svc.update_business(business_id, data, current_user)


# ── Branches ──────────────────────────────────────────────────────────────────


@router.post("/{business_id}/branches", response_model=BranchResponse, status_code=201)
async def create_branch(
    business_id: UUID,
    data: BranchCreate,
    current_user: CurrentUser,
    svc: BusinessService = Depends(_svc),
):
    return await svc.create_branch(business_id, data, current_user)


@router.get("/{business_id}/branches", response_model=list[BranchResponse])
async def list_branches(
    business_id: UUID,
    current_user: CurrentUser,
    svc: BusinessService = Depends(_svc),
):
    return await svc.list_branches(business_id, current_user)


def _staff_svc(db: AsyncSession = Depends(get_db)) -> StaffService:
    return StaffService(db)


@router.patch("/{business_id}/branches/{branch_id}", response_model=BranchResponse)
async def update_branch(
    business_id: UUID,
    branch_id: UUID,
    data: BranchUpdate,
    current_user: CurrentUser,
    svc: BusinessService = Depends(_svc),
):
    return await svc.update_branch(business_id, branch_id, data, current_user)


# ── Branch Working Hours ──────────────────────────────────────────────────────


@router.put(
    "/{business_id}/branches/{branch_id}/working-hours",
    response_model=list[WorkingHoursResponse],
)
async def set_branch_working_hours(
    business_id: UUID,
    branch_id: UUID,
    data: WorkingHoursSetRequest,
    current_user: CurrentUser,
    svc: StaffService = Depends(_staff_svc),
):
    return await svc.set_working_hours(business_id, "branch", branch_id, data.hours, current_user)


@router.get(
    "/{business_id}/branches/{branch_id}/working-hours",
    response_model=list[WorkingHoursResponse],
)
async def get_branch_working_hours(
    business_id: UUID,
    branch_id: UUID,
    svc: StaffService = Depends(_staff_svc),
):
    return await svc.get_working_hours(business_id, "branch", branch_id)
