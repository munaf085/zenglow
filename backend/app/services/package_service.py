"""
Package Service — bundled service packages, sales, and service redemption tracking.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import assert_business_access
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.package import (
    CustomerPackage,
    CustomerPackageItem,
    PackageItemTemplate,
    PackageStatus,
    PackageTemplate,
)
from app.models.service import Service
from app.models.user import User
from app.schemas.package import (
    CustomerPackageCreate,
    PackageTemplateCreate,
    PackageTemplateUpdate,
    RedeemPackageItemRequest,
)


class PackageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Package Templates ────────────────────────────────────────────────────

    async def list_templates(
        self, business_id: UUID, is_active: Optional[bool] = None
    ) -> List[PackageTemplate]:
        q = (
            select(PackageTemplate)
            .options(selectinload(PackageTemplate.items))
            .where(
                PackageTemplate.business_id == business_id,
                PackageTemplate.deleted_at.is_(None),
            )
        )
        if is_active is not None:
            q = q.where(PackageTemplate.is_active == is_active)
        q = q.order_by(PackageTemplate.price)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_template(
        self, template_id: UUID, business_id: UUID
    ) -> PackageTemplate:
        result = await self.db.execute(
            select(PackageTemplate)
            .options(selectinload(PackageTemplate.items))
            .where(
                PackageTemplate.id == template_id,
                PackageTemplate.business_id == business_id,
                PackageTemplate.deleted_at.is_(None),
            )
        )
        pkg = result.scalar_one_or_none()
        if not pkg:
            raise NotFoundError("PackageTemplate", template_id)
        return pkg

    async def create_template(
        self, business_id: UUID, data: PackageTemplateCreate, user: User
    ) -> PackageTemplate:
        assert_business_access(user, business_id)

        template = PackageTemplate(
            business_id=business_id,
            name=data.name.strip(),
            description=data.description,
            price=data.price,
            validity_days=data.validity_days,
            is_active=data.is_active,
        )
        self.db.add(template)
        await self.db.flush()

        for item in data.items:
            # Verify service exists and belongs to business
            svc_res = await self.db.execute(
                select(Service).where(
                    Service.id == item.service_id,
                    Service.business_id == business_id,
                    Service.deleted_at.is_(None),
                )
            )
            if not svc_res.scalar_one_or_none():
                raise NotFoundError("Service", item.service_id)

            pkg_item = PackageItemTemplate(
                package_template_id=template.id,
                service_id=item.service_id,
                quantity=item.quantity,
            )
            self.db.add(pkg_item)

        await self.db.flush()
        await self.db.refresh(template, ["items"])
        return template

    async def update_template(
        self, template_id: UUID, business_id: UUID, data: PackageTemplateUpdate, user: User
    ) -> PackageTemplate:
        assert_business_access(user, business_id)
        template = await self.get_template(template_id, business_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(template, key, value)

        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template, ["items"])
        return template

    # ── Customer Packages ────────────────────────────────────────────────────

    async def sell_package_to_customer(
        self, business_id: UUID, data: CustomerPackageCreate, user: User
    ) -> CustomerPackage:
        assert_business_access(user, business_id)
        template = await self.get_template(data.package_template_id, business_id)

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=template.validity_days)

        resolved_cust_id = await self._resolve_customer_id(data.customer_id)

        cust_pkg = CustomerPackage(
            business_id=business_id,
            customer_id=resolved_cust_id,
            package_template_id=template.id,
            status=PackageStatus.ACTIVE,
            purchase_date=now,
            expiry_date=expiry,
        )
        self.db.add(cust_pkg)
        await self.db.flush()

        for item in template.items:
            cp_item = CustomerPackageItem(
                customer_package_id=cust_pkg.id,
                service_id=item.service_id,
                total_quantity=item.quantity,
                used_quantity=0,
            )
            self.db.add(cp_item)

        await self.db.flush()
        await self.db.refresh(cust_pkg, ["items"])
        return cust_pkg

    async def list_customer_packages(
        self, business_id: UUID, customer_id: Optional[UUID] = None
    ) -> List[CustomerPackage]:
        q = (
            select(CustomerPackage)
            .options(
                selectinload(CustomerPackage.items),
                selectinload(CustomerPackage.package_template),
            )
            .where(
                CustomerPackage.business_id == business_id,
                CustomerPackage.deleted_at.is_(None),
            )
        )
        if customer_id:
            resolved_id = await self._resolve_customer_id(customer_id)
            q = q.where(CustomerPackage.customer_id == resolved_id)
        q = q.order_by(CustomerPackage.purchase_date.desc())
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

    async def redeem_service(
        self,
        customer_package_id: UUID,
        business_id: UUID,
        data: RedeemPackageItemRequest,
        user: User,
    ) -> CustomerPackageItem:
        assert_business_access(user, business_id)

        result = await self.db.execute(
            select(CustomerPackage)
            .options(selectinload(CustomerPackage.items))
            .where(
                CustomerPackage.id == customer_package_id,
                CustomerPackage.business_id == business_id,
                CustomerPackage.deleted_at.is_(None),
            )
        )
        pkg = result.scalar_one_or_none()
        if not pkg:
            raise NotFoundError("CustomerPackage", customer_package_id)

        if pkg.status != PackageStatus.ACTIVE:
            raise BusinessRuleError(f"Package is not active (status: {pkg.status.value})")

        now = datetime.now(timezone.utc)
        if pkg.expiry_date < now:
            pkg.status = PackageStatus.EXPIRED
            self.db.add(pkg)
            await self.db.flush()
            raise BusinessRuleError("Package has expired")

        # Find matching item
        target_item = None
        for itm in pkg.items:
            if itm.service_id == data.service_id:
                target_item = itm
                break

        if not target_item:
            raise NotFoundError("Service in package", data.service_id)

        if target_item.used_quantity >= target_item.total_quantity:
            raise BusinessRuleError("All sessions of this service in package have been redeemed")

        target_item.used_quantity += 1
        self.db.add(target_item)

        # Check if all items in package are now exhausted
        all_done = all(
            itm.used_quantity >= itm.total_quantity for itm in pkg.items
        )
        if all_done:
            pkg.status = PackageStatus.EXHAUSTED
            self.db.add(pkg)

        await self.db.flush()
        await self.db.refresh(target_item)
        return target_item
