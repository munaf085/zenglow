"""
StaffService — staff CRUD, working hours, leaves.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import assert_business_access
from app.core.exceptions import NotFoundError, TenantIsolationError
from app.core.logging import get_logger
from app.models.staff import Staff, StaffLeave, StaffService as StaffServiceModel, WorkingHours
from app.models.user import User
from app.schemas.staff import StaffCreate, StaffLeaveCreate, StaffUpdate, WorkingHoursEntry

logger = get_logger(__name__)


class StaffService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_staff(self, business_id: UUID, data: StaffCreate, user: User) -> Staff:
        assert_business_access(user, business_id)

        # Feature flag: check plan allows more staff
        from app.core.feature_flags import check_staff_limit
        from sqlalchemy import func
        count_result = await self.db.execute(
            select(func.count(Staff.id)).where(
                Staff.business_id == business_id,
                Staff.deleted_at.is_(None),
            )
        )
        current_count = count_result.scalar_one()
        await check_staff_limit(business_id, current_count, self.db)

        staff = Staff(
            business_id=business_id,
            branch_id=data.branch_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            title=data.title,
            bio=data.bio,
            bookable=data.bookable,
            sort_order=data.sort_order,
        )
        self.db.add(staff)
        await self.db.flush()

        # Assign services
        for service_id in data.service_ids:
            link = StaffServiceModel(staff_id=staff.id, service_id=service_id)
            self.db.add(link)

        # Default working hours (same as business defaults)
        for day in range(7):
            wh = WorkingHours(
                entity_type="staff",
                entity_id=staff.id,
                business_id=business_id,
                day_of_week=day,
                is_open=day < 6,
                open_time="09:00" if day < 6 else None,
                close_time="18:00" if day < 6 else None,
            )
            self.db.add(wh)

        await self.db.flush()
        return staff

    async def get_staff(self, business_id: UUID, staff_id: UUID, user: User) -> Staff:
        assert_business_access(user, business_id)
        staff = await self._get_staff_tenant(business_id, staff_id)
        return staff

    async def list_staff(self, business_id: UUID, user: User) -> List[Staff]:
        assert_business_access(user, business_id)
        result = await self.db.execute(
            select(Staff).where(
                Staff.business_id == business_id, Staff.deleted_at.is_(None)
            ).order_by(Staff.sort_order, Staff.first_name)
        )
        return list(result.scalars().all())

    async def update_staff(
        self, business_id: UUID, staff_id: UUID, data: StaffUpdate, user: User
    ) -> Staff:
        assert_business_access(user, business_id)
        staff = await self._get_staff_tenant(business_id, staff_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(staff, key, value)

        self.db.add(staff)
        await self.db.flush()
        return staff

    async def delete_staff(self, business_id: UUID, staff_id: UUID, user: User) -> None:
        assert_business_access(user, business_id)
        staff = await self._get_staff_tenant(business_id, staff_id)
        staff.soft_delete()
        self.db.add(staff)
        await self.db.flush()

    async def assign_services(
        self, business_id: UUID, staff_id: UUID, service_ids: List[UUID], user: User
    ) -> None:
        assert_business_access(user, business_id)
        await self._get_staff_tenant(business_id, staff_id)

        # Remove existing and re-assign
        await self.db.execute(
            delete(StaffServiceModel).where(StaffServiceModel.staff_id == staff_id)
        )
        for service_id in service_ids:
            link = StaffServiceModel(staff_id=staff_id, service_id=service_id)
            self.db.add(link)
        await self.db.flush()

    async def set_working_hours(
        self,
        business_id: UUID,
        entity_type: str,
        entity_id: UUID,
        hours: List[WorkingHoursEntry],
        user: User,
    ) -> List[WorkingHours]:
        assert_business_access(user, business_id)

        # Delete and recreate
        await self.db.execute(
            delete(WorkingHours).where(
                WorkingHours.entity_type == entity_type,
                WorkingHours.entity_id == entity_id,
                WorkingHours.business_id == business_id,
            )
        )
        results = []
        for entry in hours:
            wh = WorkingHours(
                entity_type=entity_type,
                entity_id=entity_id,
                business_id=business_id,
                day_of_week=entry.day_of_week,
                is_open=entry.is_open,
                open_time=entry.open_time,
                close_time=entry.close_time,
                break_start=entry.break_start,
                break_end=entry.break_end,
            )
            self.db.add(wh)
            results.append(wh)

        await self.db.flush()
        return results

    async def get_working_hours(
        self, business_id: UUID, entity_type: str, entity_id: UUID
    ) -> List[WorkingHours]:
        result = await self.db.execute(
            select(WorkingHours).where(
                WorkingHours.entity_type == entity_type,
                WorkingHours.entity_id == entity_id,
                WorkingHours.business_id == business_id,
            ).order_by(WorkingHours.day_of_week)
        )
        return list(result.scalars().all())

    async def create_leave(
        self, business_id: UUID, staff_id: UUID, data: StaffLeaveCreate, user: User
    ) -> StaffLeave:
        assert_business_access(user, business_id)
        await self._get_staff_tenant(business_id, staff_id)

        leave = StaffLeave(
            staff_id=staff_id,
            business_id=business_id,
            leave_type=data.leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason,
            approved=True,
        )
        self.db.add(leave)
        await self.db.flush()
        return leave

    async def list_leaves(self, business_id: UUID, staff_id: UUID) -> List[StaffLeave]:
        result = await self.db.execute(
            select(StaffLeave).where(
                StaffLeave.staff_id == staff_id, StaffLeave.business_id == business_id
            )
        )
        return list(result.scalars().all())

    async def _get_staff_tenant(self, business_id: UUID, staff_id: UUID) -> Staff:
        result = await self.db.execute(
            select(Staff).where(
                Staff.id == staff_id,
                Staff.business_id == business_id,
                Staff.deleted_at.is_(None),
            )
        )
        staff = result.scalar_one_or_none()
        if not staff:
            raise NotFoundError("Staff", staff_id)
        return staff
