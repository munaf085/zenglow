"""
ServiceCatalogService — service and category CRUD.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import assert_business_access
from app.core.exceptions import NotFoundError, TenantIsolationError
from app.models.service import Service, ServiceCategory
from app.models.user import User
from app.schemas.service import (
    ServiceCategoryCreate,
    ServiceCategoryUpdate,
    ServiceCreate,
    ServiceUpdate,
)


class ServiceCatalogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Categories ────────────────────────────────────────────────────────────

    async def create_category(
        self, business_id: UUID, data: ServiceCategoryCreate, user: User
    ) -> ServiceCategory:
        assert_business_access(user, business_id)
        cat = ServiceCategory(business_id=business_id, **data.model_dump())
        self.db.add(cat)
        await self.db.flush()
        return cat

    async def list_categories(self, business_id: UUID) -> List[ServiceCategory]:
        result = await self.db.execute(
            select(ServiceCategory).where(
                ServiceCategory.business_id == business_id,
                ServiceCategory.deleted_at.is_(None),
            ).order_by(ServiceCategory.sort_order, ServiceCategory.name)
        )
        return list(result.scalars().all())

    async def update_category(
        self, business_id: UUID, cat_id: UUID, data: ServiceCategoryUpdate, user: User
    ) -> ServiceCategory:
        assert_business_access(user, business_id)
        cat = await self._get_category_tenant(business_id, cat_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(cat, k, v)
        self.db.add(cat)
        await self.db.flush()
        return cat

    async def delete_category(self, business_id: UUID, cat_id: UUID, user: User) -> None:
        assert_business_access(user, business_id)
        cat = await self._get_category_tenant(business_id, cat_id)
        cat.soft_delete()
        self.db.add(cat)
        await self.db.flush()

    # ── Services ──────────────────────────────────────────────────────────────

    async def create_service(
        self, business_id: UUID, data: ServiceCreate, user: User
    ) -> Service:
        assert_business_access(user, business_id)
        service = Service(
            business_id=business_id,
            category_id=data.category_id,
            name=data.name,
            description=data.description,
            price=data.price,
            tax_rate=data.tax_rate,
            duration_minutes=data.duration_minutes,
            buffer_before_minutes=data.buffer_before_minutes,
            buffer_after_minutes=data.buffer_after_minutes,
            is_active=data.is_active,
            online_booking_enabled=data.online_booking_enabled,
            sort_order=data.sort_order,
        )
        self.db.add(service)
        await self.db.flush()

        # Assign staff
        if data.staff_ids:
            from app.models.staff import StaffService as StaffServiceModel
            for staff_id in data.staff_ids:
                link = StaffServiceModel(staff_id=staff_id, service_id=service.id)
                self.db.add(link)
            await self.db.flush()

        return service

    async def list_services(
        self, business_id: UUID, category_id: Optional[UUID] = None, active_only: bool = True
    ) -> List[Service]:
        q = select(Service).where(
            Service.business_id == business_id, Service.deleted_at.is_(None)
        )
        if active_only:
            q = q.where(Service.is_active.is_(True))
        if category_id:
            q = q.where(Service.category_id == category_id)
        q = q.order_by(Service.sort_order, Service.name)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_service(self, business_id: UUID, service_id: UUID) -> Service:
        return await self._get_service_tenant(business_id, service_id)

    async def update_service(
        self, business_id: UUID, service_id: UUID, data: ServiceUpdate, user: User
    ) -> Service:
        assert_business_access(user, business_id)
        service = await self._get_service_tenant(business_id, service_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(service, k, v)
        self.db.add(service)
        await self.db.flush()
        return service

    async def delete_service(self, business_id: UUID, service_id: UUID, user: User) -> None:
        assert_business_access(user, business_id)
        service = await self._get_service_tenant(business_id, service_id)
        service.soft_delete()
        self.db.add(service)
        await self.db.flush()

    async def _get_category_tenant(self, business_id: UUID, cat_id: UUID) -> ServiceCategory:
        result = await self.db.execute(
            select(ServiceCategory).where(
                ServiceCategory.id == cat_id,
                ServiceCategory.business_id == business_id,
                ServiceCategory.deleted_at.is_(None),
            )
        )
        cat = result.scalar_one_or_none()
        if not cat:
            raise NotFoundError("ServiceCategory", cat_id)
        return cat

    async def _get_service_tenant(self, business_id: UUID, service_id: UUID) -> Service:
        result = await self.db.execute(
            select(Service).where(
                Service.id == service_id,
                Service.business_id == business_id,
                Service.deleted_at.is_(None),
            )
        )
        svc = result.scalar_one_or_none()
        if not svc:
            raise NotFoundError("Service", service_id)
        return svc
