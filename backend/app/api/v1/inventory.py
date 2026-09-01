"""
Inventory & Products API Endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.inventory import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StockMovementCreate,
    StockMovementResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/businesses/{business_id}/inventory", tags=["inventory"])


def get_inventory_service(db: AsyncSession = Depends(get_db)) -> InventoryService:
    return InventoryService(db)


# ── Categories ───────────────────────────────────────────────────────────────

@router.get("/categories", response_model=List[ProductCategoryResponse])
async def list_categories(
    business_id: UUID,
    svc: InventoryService = Depends(get_inventory_service),
):
    """List product categories for a business."""
    return await svc.list_categories(business_id)


@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    business_id: UUID,
    data: ProductCategoryCreate,
    user: CurrentUser,
    svc: InventoryService = Depends(get_inventory_service),
):
    """Create a new product category."""
    return await svc.create_category(business_id, data, user)


# ── Products ─────────────────────────────────────────────────────────────────

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    business_id: UUID,
    category_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    low_stock_only: bool = Query(False),
    svc: InventoryService = Depends(get_inventory_service),
):
    """List products with optional category, active, and low-stock filters."""
    products = await svc.list_products(business_id, category_id, is_active, low_stock_only)
    resp = []
    for p in products:
        p_resp = ProductResponse.model_validate(p)
        p_resp.is_low_stock = p.stock_quantity <= p.low_stock_threshold
        resp.append(p_resp)
    return resp


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    business_id: UUID,
    data: ProductCreate,
    user: CurrentUser,
    svc: InventoryService = Depends(get_inventory_service),
):
    """Create a new product in the inventory catalog."""
    p = await svc.create_product(business_id, data, user)
    p_resp = ProductResponse.model_validate(p)
    p_resp.is_low_stock = p.stock_quantity <= p.low_stock_threshold
    return p_resp


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    business_id: UUID,
    product_id: UUID,
    svc: InventoryService = Depends(get_inventory_service),
):
    """Get single product details."""
    p = await svc.get_product(product_id, business_id)
    p_resp = ProductResponse.model_validate(p)
    p_resp.is_low_stock = p.stock_quantity <= p.low_stock_threshold
    return p_resp


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    business_id: UUID,
    product_id: UUID,
    data: ProductUpdate,
    user: CurrentUser,
    svc: InventoryService = Depends(get_inventory_service),
):
    """Update product information or thresholds."""
    p = await svc.update_product(product_id, business_id, data, user)
    p_resp = ProductResponse.model_validate(p)
    p_resp.is_low_stock = p.stock_quantity <= p.low_stock_threshold
    return p_resp


# ── Stock Adjustments & Movements ────────────────────────────────────────────

@router.post("/movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
async def record_stock_movement(
    business_id: UUID,
    data: StockMovementCreate,
    user: CurrentUser,
    svc: InventoryService = Depends(get_inventory_service),
):
    """Record a stock adjustment, restock, or write-off."""
    return await svc.record_stock_movement(business_id, data, user)


@router.get("/movements", response_model=List[StockMovementResponse])
async def list_stock_movements(
    business_id: UUID,
    product_id: Optional[UUID] = None,
    user: CurrentUser = None,
    svc: InventoryService = Depends(get_inventory_service),
):
    """View stock adjustment and movement audit history."""
    return await svc.list_movements(business_id, product_id)
