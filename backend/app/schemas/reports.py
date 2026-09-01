"""
Reports & Business Analytics Schemas.
"""
from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class RevenueReportResponse(BaseModel):
    total_revenue: float
    service_revenue: float
    product_revenue: float
    other_revenue: float
    total_tax: float
    total_discounts: float
    total_tips: float
    total_orders: int
    daily_breakdown: List[Dict[str, float]] = []


class StaffPerformanceMetric(BaseModel):
    staff_id: UUID
    staff_name: str
    appointments_count: int
    services_revenue: float
    products_revenue: float
    total_revenue: float
    tips_earned: float


class StaffPerformanceResponse(BaseModel):
    metrics: List[StaffPerformanceMetric] = []


class InventoryReportItem(BaseModel):
    product_id: UUID
    name: str
    sku: Optional[str] = None
    stock_quantity: int
    cost_price: float
    retail_price: float
    stock_valuation_cost: float
    stock_valuation_retail: float
    is_low_stock: bool


class InventoryReportResponse(BaseModel):
    total_items: int
    total_valuation_cost: float
    total_valuation_retail: float
    low_stock_count: int
    items: List[InventoryReportItem] = []


class OperationsSummaryResponse(BaseModel):
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    no_show_bookings: int
    cancellation_rate: float
    active_memberships: int
    active_packages: int
