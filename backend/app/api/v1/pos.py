"""
POS & Point-of-Sale Checkout API Endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.pos import (
    OrderItemResponse,
    OrderPaymentResponse,
    OrderResponse,
    POSCheckoutRequest,
)
from app.services.pos_service import POSService

router = APIRouter(prefix="/businesses/{business_id}/pos", tags=["pos"])


def get_pos_service(db: AsyncSession = Depends(get_db)) -> POSService:
    return POSService(db)


@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def pos_checkout(
    business_id: UUID,
    data: POSCheckoutRequest,
    user: CurrentUser,
    svc: POSService = Depends(get_pos_service),
):
    """Complete a POS checkout sale with multi-tender payment support."""
    order = await svc.checkout(business_id, data, user)
    return OrderResponse.model_validate(order)


@router.get("/orders", response_model=List[OrderResponse])
async def list_pos_orders(
    business_id: UUID,
    branch_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
    user: CurrentUser = None,
    svc: POSService = Depends(get_pos_service),
):
    """List completed and past POS orders."""
    orders = await svc.list_orders(business_id, branch_id, customer_id)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_pos_order(
    business_id: UUID,
    order_id: UUID,
    user: CurrentUser = None,
    svc: POSService = Depends(get_pos_service),
):
    """Get single order receipt details."""
    order = await svc.get_order(order_id, business_id)
    return OrderResponse.model_validate(order)
