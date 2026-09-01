"""
Staff management endpoints.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.staff import (
    StaffCreate,
    StaffLeaveCreate,
    StaffLeaveResponse,
    StaffResponse,
    StaffUpdate,
    WorkingHoursResponse,
    WorkingHoursSetRequest,
)
from app.services.staff_service import StaffService

router = APIRouter(prefix="/businesses/{business_id}/staff", tags=["staff"])


def _svc(db: AsyncSession = Depends(get_db)) -> StaffService:
    return StaffService(db)


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    business_id: UUID,
    data: StaffCreate,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.create_staff(business_id, data, current_user)


@router.get("", response_model=List[StaffResponse])
async def list_staff(
    business_id: UUID,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.list_staff(business_id, current_user)


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    business_id: UUID,
    staff_id: UUID,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.get_staff(business_id, staff_id, current_user)


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    business_id: UUID,
    staff_id: UUID,
    data: StaffUpdate,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.update_staff(business_id, staff_id, data, current_user)


@router.delete("/{staff_id}", response_model=MessageResponse)
async def delete_staff(
    business_id: UUID,
    staff_id: UUID,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    await svc.delete_staff(business_id, staff_id, current_user)
    return {"message": "Staff member deactivated"}


@router.put("/{staff_id}/working-hours", response_model=List[WorkingHoursResponse])
async def set_staff_working_hours(
    business_id: UUID,
    staff_id: UUID,
    data: WorkingHoursSetRequest,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.set_working_hours(business_id, "staff", staff_id, data.hours, current_user)


@router.get("/{staff_id}/working-hours", response_model=List[WorkingHoursResponse])
async def get_staff_working_hours(
    business_id: UUID,
    staff_id: UUID,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.get_working_hours(business_id, "staff", staff_id)


@router.post("/{staff_id}/leaves", response_model=StaffLeaveResponse, status_code=201)
async def create_leave(
    business_id: UUID,
    staff_id: UUID,
    data: StaffLeaveCreate,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.create_leave(business_id, staff_id, data, current_user)


@router.get("/{staff_id}/leaves", response_model=List[StaffLeaveResponse])
async def list_leaves(
    business_id: UUID,
    staff_id: UUID,
    current_user: CurrentUser,
    svc: StaffService = Depends(_svc),
):
    return await svc.list_leaves(business_id, staff_id)
