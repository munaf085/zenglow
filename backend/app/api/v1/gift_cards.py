"""
Gift Cards API Endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.gift_card import (
    GiftCardBalanceCheckResponse,
    GiftCardCreate,
    GiftCardRedeemRequest,
    GiftCardResponse,
)
from app.services.gift_card_service import GiftCardService

router = APIRouter(prefix="/businesses/{business_id}/gift-cards", tags=["gift-cards"])


def get_gift_card_service(db: AsyncSession = Depends(get_db)) -> GiftCardService:
    return GiftCardService(db)


@router.post("", response_model=GiftCardResponse, status_code=status.HTTP_201_CREATED)
async def issue_gift_card(
    business_id: UUID,
    data: GiftCardCreate,
    user: CurrentUser,
    svc: GiftCardService = Depends(get_gift_card_service),
):
    """Issue a new digital gift card with unique code."""
    return await svc.issue_gift_card(business_id, data, user)


@router.get("", response_model=List[GiftCardResponse])
async def list_gift_cards(
    business_id: UUID,
    is_active: Optional[bool] = None,
    user: CurrentUser = None,
    svc: GiftCardService = Depends(get_gift_card_service),
):
    """List issued gift cards."""
    return await svc.list_gift_cards(business_id, is_active)


@router.get("/check/{code}", response_model=GiftCardBalanceCheckResponse)
async def check_gift_card_balance(
    business_id: UUID,
    code: str,
    svc: GiftCardService = Depends(get_gift_card_service),
):
    """Check balance and validity of a gift card by code."""
    card = await svc.check_balance(code, business_id)
    return GiftCardBalanceCheckResponse(
        valid=card.is_active,
        code=card.code,
        current_balance=card.current_balance,
        expiry_date=card.expiry_date,
        recipient_name=card.recipient_name,
    )


@router.post("/redeem", response_model=GiftCardResponse)
async def redeem_gift_card(
    business_id: UUID,
    data: GiftCardRedeemRequest,
    user: CurrentUser,
    svc: GiftCardService = Depends(get_gift_card_service),
):
    """Redeem balance from a gift card."""
    return await svc.redeem_gift_card(business_id, data, user)
