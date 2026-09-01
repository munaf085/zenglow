"""
Report Service — financial summaries, staff metrics, inventory valuations, and booking operations stats.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import assert_business_access
from app.models.appointment import Appointment, AppointmentStatus
from app.models.inventory import Product
from app.models.membership import CustomerMembership, MembershipStatus
from app.models.package import CustomerPackage, PackageStatus
from app.models.pos import Order, OrderItem, OrderItemType, OrderStatus
from app.models.staff import Staff
from app.models.user import User
from app.schemas.reports import (
    InventoryReportItem,
    InventoryReportResponse,
    OperationsSummaryResponse,
    RevenueReportResponse,
    StaffPerformanceMetric,
    StaffPerformanceResponse,
)


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_revenue_report(
        self,
        business_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user: Optional[User] = None,
    ) -> RevenueReportResponse:
        if user:
            assert_business_access(user, business_id)

        q = select(Order).where(
            Order.business_id == business_id,
            Order.status == OrderStatus.COMPLETED,
            Order.deleted_at.is_(None),
        )
        if start_date:
            q = q.where(Order.created_at >= start_date)
        if end_date:
            q = q.where(Order.created_at <= end_date)

        result = await self.db.execute(q)
        orders = list(result.scalars().all())

        total_revenue = 0.0
        service_rev = 0.0
        product_rev = 0.0
        other_rev = 0.0
        total_tax = 0.0
        total_discounts = 0.0
        total_tips = 0.0
        daily_map: Dict[str, float] = {}

        for o in orders:
            total_revenue += float(o.total_amount)
            total_tax += float(o.tax_amount)
            total_discounts += float(o.discount_amount)
            total_tips += float(o.tip_amount)

            day_str = o.created_at.strftime("%Y-%m-%d")
            daily_map[day_str] = daily_map.get(day_str, 0.0) + float(o.total_amount)

            for itm in o.items:
                if itm.item_type == OrderItemType.SERVICE:
                    service_rev += float(itm.total_price)
                elif itm.item_type == OrderItemType.PRODUCT:
                    product_rev += float(itm.total_price)
                else:
                    other_rev += float(itm.total_price)

        daily_list = [{"date": k, "revenue": round(v, 2)} for k, v in sorted(daily_map.items())]

        return RevenueReportResponse(
            total_revenue=round(total_revenue, 2),
            service_revenue=round(service_rev, 2),
            product_revenue=round(product_rev, 2),
            other_revenue=round(other_rev, 2),
            total_tax=round(total_tax, 2),
            total_discounts=round(total_discounts, 2),
            total_tips=round(total_tips, 2),
            total_orders=len(orders),
            daily_breakdown=daily_list,
        )

    async def get_staff_performance(
        self,
        business_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user: Optional[User] = None,
    ) -> StaffPerformanceResponse:
        if user:
            assert_business_access(user, business_id)

        # Get all staff
        staff_res = await self.db.execute(
            select(Staff).where(
                Staff.business_id == business_id,
                Staff.deleted_at.is_(None),
            )
        )
        staff_list = list(staff_res.scalars().all())

        metrics = []
        for s in staff_list:
            orders_q = select(Order).where(
                Order.business_id == business_id,
                Order.staff_id == s.id,
                Order.status == OrderStatus.COMPLETED,
            )
            if start_date:
                orders_q = orders_q.where(Order.created_at >= start_date)
            if end_date:
                orders_q = orders_q.where(Order.created_at <= end_date)

            orders_res = await self.db.execute(orders_q)
            staff_orders = list(orders_res.scalars().all())

            appts_count = len(staff_orders)
            srv_rev = 0.0
            prd_rev = 0.0
            tips = sum(float(o.tip_amount) for o in staff_orders)
            tot = sum(float(o.total_amount) for o in staff_orders)

            for o in staff_orders:
                for itm in o.items:
                    if itm.item_type == OrderItemType.SERVICE:
                        srv_rev += float(itm.total_price)
                    elif itm.item_type == OrderItemType.PRODUCT:
                        prd_rev += float(itm.total_price)

            metrics.append(
                StaffPerformanceMetric(
                    staff_id=s.id,
                    staff_name=f"{s.first_name} {s.last_name or ''}".strip(),
                    appointments_count=appts_count,
                    services_revenue=round(srv_rev, 2),
                    products_revenue=round(prd_rev, 2),
                    total_revenue=round(tot, 2),
                    tips_earned=round(tips, 2),
                )
            )

        return StaffPerformanceResponse(metrics=metrics)

    async def get_inventory_report(
        self, business_id: UUID, user: Optional[User] = None
    ) -> InventoryReportResponse:
        if user:
            assert_business_access(user, business_id)

        res = await self.db.execute(
            select(Product).where(
                Product.business_id == business_id,
                Product.deleted_at.is_(None),
            )
        )
        products = list(res.scalars().all())

        items = []
        tot_cost = 0.0
        tot_retail = 0.0
        low_stock_count = 0

        for p in products:
            c_val = p.stock_quantity * float(p.cost_price)
            r_val = p.stock_quantity * float(p.retail_price)
            tot_cost += c_val
            tot_retail += r_val
            is_low = p.stock_quantity <= p.low_stock_threshold
            if is_low:
                low_stock_count += 1

            items.append(
                InventoryReportItem(
                    product_id=p.id,
                    name=p.name,
                    sku=p.sku,
                    stock_quantity=p.stock_quantity,
                    cost_price=float(p.cost_price),
                    retail_price=float(p.retail_price),
                    stock_valuation_cost=round(c_val, 2),
                    stock_valuation_retail=round(r_val, 2),
                    is_low_stock=is_low,
                )
            )

        return InventoryReportResponse(
            total_items=len(products),
            total_valuation_cost=round(tot_cost, 2),
            total_valuation_retail=round(tot_retail, 2),
            low_stock_count=low_stock_count,
            items=items,
        )

    async def get_operations_summary(
        self, business_id: UUID, user: Optional[User] = None
    ) -> OperationsSummaryResponse:
        if user:
            assert_business_access(user, business_id)

        # Booking counts
        appts_res = await self.db.execute(
            select(Appointment).where(
                Appointment.business_id == business_id,
                Appointment.deleted_at.is_(None),
            )
        )
        appts = list(appts_res.scalars().all())
        total_b = len(appts)
        completed_b = sum(1 for a in appts if a.status == AppointmentStatus.COMPLETED)
        cancelled_b = sum(1 for a in appts if a.status == AppointmentStatus.CANCELLED)
        noshow_b = sum(1 for a in appts if a.status == AppointmentStatus.NO_SHOW)
        cancellation_rate = round((cancelled_b / total_b * 100.0) if total_b > 0 else 0.0, 2)

        # Active memberships
        mem_res = await self.db.execute(
            select(func.count(CustomerMembership.id)).where(
                CustomerMembership.business_id == business_id,
                CustomerMembership.status == MembershipStatus.ACTIVE,
                CustomerMembership.deleted_at.is_(None),
            )
        )
        active_mems = mem_res.scalar_one()

        # Active packages
        pkg_res = await self.db.execute(
            select(func.count(CustomerPackage.id)).where(
                CustomerPackage.business_id == business_id,
                CustomerPackage.status == PackageStatus.ACTIVE,
                CustomerPackage.deleted_at.is_(None),
            )
        )
        active_pkgs = pkg_res.scalar_one()

        return OperationsSummaryResponse(
            total_bookings=total_b,
            completed_bookings=completed_b,
            cancelled_bookings=cancelled_b,
            no_show_bookings=noshow_b,
            cancellation_rate=cancellation_rate,
            active_memberships=active_mems,
            active_packages=active_pkgs,
        )
