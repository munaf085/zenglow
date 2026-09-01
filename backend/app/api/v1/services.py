"""
Service catalog endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.schemas.common import MessageResponse
from app.schemas.service import (
    ServiceCategoryCreate,
    ServiceCategoryResponse,
    ServiceCategoryUpdate,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.services.service_service import ServiceCatalogService

router = APIRouter(prefix="/businesses/{business_id}/services", tags=["services"])


def _svc(db: AsyncSession = Depends(get_db)) -> ServiceCatalogService:
    return ServiceCatalogService(db)


# ── Categories ────────────────────────────────────────────────────────────────


@router.post("/categories", response_model=ServiceCategoryResponse, status_code=201)
async def create_category(
    business_id: UUID,
    data: ServiceCategoryCreate,
    current_user: CurrentUser,
    svc: ServiceCatalogService = Depends(_svc),
):
    return await svc.create_category(business_id, data, current_user)


@router.get("/categories", response_model=List[ServiceCategoryResponse])
async def list_categories(
    business_id: UUID,
    svc: ServiceCatalogService = Depends(_svc),
):
    return await svc.list_categories(business_id)


@router.patch("/categories/{cat_id}", response_model=ServiceCategoryResponse)
async def update_category(
    business_id: UUID,
    cat_id: UUID,
    data: ServiceCategoryUpdate,
    current_user: CurrentUser,
    svc: ServiceCatalogService = Depends(_svc),
):
    return await svc.update_category(business_id, cat_id, data, current_user)


@router.delete("/categories/{cat_id}", response_model=MessageResponse)
async def delete_category(
    business_id: UUID,
    cat_id: UUID,
    current_user: CurrentUser,
    svc: ServiceCatalogService = Depends(_svc),
):
    await svc.delete_category(business_id, cat_id, current_user)
    return {"message": "Category deleted"}


# ── Services ──────────────────────────────────────────────────────────────────


@router.post("", response_model=ServiceResponse, status_code=201)
async def create_service(
    business_id: UUID,
    data: ServiceCreate,
    current_user: CurrentUser,
    svc: ServiceCatalogService = Depends(_svc),
):
    return await svc.create_service(business_id, data, current_user)


@router.get("", response_model=List[ServiceResponse])
async def list_services(
    business_id: UUID,
    category_id: Optional[UUID] = Query(default=None),
    active_only: bool = Query(default=True),
    svc: ServiceCatalogService = Depends(_svc),
):
    return await svc.list_services(business_id, category_id, active_only)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    business_id: UUID,
    service_id: UUID,
    svc: ServiceCatalogService = Depends(_svc),
):
    return await svc.get_service(business_id, service_id)


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    business_id: UUID,
    service_id: UUID,
    data: ServiceUpdate,
    current_user: CurrentUser,
    svc: ServiceCatalogService = Depends(_svc),
):
    return await svc.update_service(business_id, service_id, data, current_user)


@router.delete("/{service_id}", response_model=MessageResponse)
async def delete_service(
    business_id: UUID,
    service_id: UUID,
    current_user: CurrentUser,
    svc: ServiceCatalogService = Depends(_svc),
):
    await svc.delete_service(business_id, service_id, current_user)
    return {"message": "Service deleted"}
