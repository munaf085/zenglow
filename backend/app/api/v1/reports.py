"""
Reports & Analytics API Endpoints.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.reports import (
    InventoryReportResponse,
    OperationsSummaryResponse,
    RevenueReportResponse,
    StaffPerformanceResponse,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/businesses/{business_id}/reports", tags=["reports"])


def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db)


@router.get("/revenue", response_model=RevenueReportResponse)
async def get_revenue_report(
    business_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: CurrentUser = None,
    svc: ReportService = Depends(get_report_service),
):
    """Get financial revenue summary broken down by services, products, and days."""
    return await svc.get_revenue_report(business_id, start_date, end_date, user)


@router.get("/staff", response_model=StaffPerformanceResponse)
async def get_staff_performance(
    business_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: CurrentUser = None,
    svc: ReportService = Depends(get_report_service),
):
    """Get staff utilization, sales performance, and tip metrics."""
    return await svc.get_staff_performance(business_id, start_date, end_date, user)


@router.get("/inventory", response_model=InventoryReportResponse)
async def get_inventory_report(
    business_id: UUID,
    user: CurrentUser = None,
    svc: ReportService = Depends(get_report_service),
):
    """Get stock valuation and low-stock alerts."""
    return await svc.get_inventory_report(business_id, user)


@router.get("/operations", response_model=OperationsSummaryResponse)
async def get_operations_summary(
    business_id: UUID,
    user: CurrentUser = None,
    svc: ReportService = Depends(get_report_service),
):
    """Get booking operations summary, cancellation rates, and active membership/package statistics."""
    return await svc.get_operations_summary(business_id, user)
