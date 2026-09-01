"""
Packages API Endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.package import (
    CustomerPackageCreate,
    CustomerPackageItemResponse,
    CustomerPackageResponse,
    PackageTemplateCreate,
    PackageTemplateResponse,
    PackageTemplateUpdate,
    RedeemPackageItemRequest,
)
from app.services.package_service import PackageService

router = APIRouter(prefix="/businesses/{business_id}/packages", tags=["packages"])


def get_package_service(db: AsyncSession = Depends(get_db)) -> PackageService:
    return PackageService(db)


# ── Templates ────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=List[PackageTemplateResponse])
async def list_package_templates(
    business_id: UUID,
    is_active: Optional[bool] = None,
    svc: PackageService = Depends(get_package_service),
):
    """List bundled service package templates."""
    return await svc.list_templates(business_id, is_active)


@router.post("/templates", response_model=PackageTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_package_template(
    business_id: UUID,
    data: PackageTemplateCreate,
    user: CurrentUser,
    svc: PackageService = Depends(get_package_service),
):
    """Create a new bundled service package template."""
    return await svc.create_template(business_id, data, user)


@router.patch("/templates/{template_id}", response_model=PackageTemplateResponse)
async def update_package_template(
    business_id: UUID,
    template_id: UUID,
    data: PackageTemplateUpdate,
    user: CurrentUser,
    svc: PackageService = Depends(get_package_service),
):
    """Update a package template."""
    return await svc.update_template(template_id, business_id, data, user)


# ── Customer Packages ────────────────────────────────────────────────────────

@router.post("/sell", response_model=CustomerPackageResponse, status_code=status.HTTP_201_CREATED)
async def sell_package_to_customer(
    business_id: UUID,
    data: CustomerPackageCreate,
    user: CurrentUser,
    svc: PackageService = Depends(get_package_service),
):
    """Sell/assign a bundled service package to a customer."""
    pkg = await svc.sell_package_to_customer(business_id, data, user)
    # Populate remaining_quantity on items
    resp = CustomerPackageResponse.model_validate(pkg)
    for itm in resp.items:
        itm.remaining_quantity = max(0, itm.total_quantity - itm.used_quantity)
    return resp


@router.get("/customers", response_model=List[CustomerPackageResponse])
async def list_customer_packages(
    business_id: UUID,
    customer_id: Optional[UUID] = None,
    svc: PackageService = Depends(get_package_service),
):
    """List customer packages and remaining sessions."""
    pkgs = await svc.list_customer_packages(business_id, customer_id)
    result = []
    for pkg in pkgs:
        resp = CustomerPackageResponse.model_validate(pkg)
        for itm in resp.items:
            itm.remaining_quantity = max(0, itm.total_quantity - itm.used_quantity)
        result.append(resp)
    return result


@router.post("/customers/{customer_package_id}/redeem", response_model=CustomerPackageItemResponse)
async def redeem_package_service(
    business_id: UUID,
    customer_package_id: UUID,
    data: RedeemPackageItemRequest,
    user: CurrentUser,
    svc: PackageService = Depends(get_package_service),
):
    """Redeem one session of a service from a customer's package."""
    itm = await svc.redeem_service(customer_package_id, business_id, data, user)
    resp = CustomerPackageItemResponse.model_validate(itm)
    resp.remaining_quantity = max(0, resp.total_quantity - resp.used_quantity)
    return resp
