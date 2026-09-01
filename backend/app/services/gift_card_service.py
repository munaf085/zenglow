"""
Gift Card Service — code generation, issuance, balance checks, and redemption ledger.
"""
import random
import string
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import assert_business_access
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.gift_card import (
    GiftCard,
    GiftCardTransaction,
    GiftCardTransactionType,
)
from app.models.user import User
from app.schemas.gift_card import GiftCardCreate, GiftCardRedeemRequest


def _generate_gift_card_code() -> str:
    """Generate a clean readable 12-char gift card code: GC-XXXX-XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    p1 = "".join(random.choices(chars, k=4))
    p2 = "".join(random.choices(chars, k=4))
    return f"GC-{p1}-{p2}"


class GiftCardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def issue_gift_card(
        self, business_id: UUID, data: GiftCardCreate, user: User
    ) -> GiftCard:
        assert_business_access(user, business_id)

        # Generate unique code
        code = _generate_gift_card_code()
        expiry_date = None
        if data.expiry_days:
            expiry_date = datetime.now(timezone.utc) + timedelta(days=data.expiry_days)

        card = GiftCard(
            business_id=business_id,
            code=code,
            initial_balance=data.amount,
            current_balance=data.amount,
            recipient_name=data.recipient_name,
            recipient_email=data.recipient_email,
            recipient_phone=data.recipient_phone,
            message=data.message,
            purchaser_customer_id=data.purchaser_customer_id,
            expiry_date=expiry_date,
            is_active=True,
        )
        self.db.add(card)
        await self.db.flush()

        # Record initial purchase transaction
        tx = GiftCardTransaction(
            gift_card_id=card.id,
            transaction_type=GiftCardTransactionType.PURCHASE,
            amount=data.amount,
            balance_after=data.amount,
            notes="Initial gift card issuance",
        )
        self.db.add(tx)
        await self.db.flush()
        await self.db.refresh(card)
        return card

    async def check_balance(self, code: str, business_id: UUID) -> GiftCard:
        result = await self.db.execute(
            select(GiftCard).where(
                GiftCard.code == code.strip().upper(),
                GiftCard.business_id == business_id,
                GiftCard.deleted_at.is_(None),
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            raise NotFoundError("GiftCard", code)

        now = datetime.now(timezone.utc)
        if not card.is_active:
            raise BusinessRuleError("Gift card is inactive or has been disabled")
        if card.expiry_date and card.expiry_date < now:
            raise BusinessRuleError("Gift card has expired")

        return card

    async def redeem_gift_card(
        self, business_id: UUID, data: GiftCardRedeemRequest, user: User
    ) -> GiftCard:
        assert_business_access(user, business_id)
        card = await self.check_balance(data.code, business_id)

        current_bal = float(card.current_balance)
        req_amount = float(data.amount)

        if current_bal < req_amount:
            raise BusinessRuleError(
                f"Insufficient gift card balance. Available: ₹{current_bal:.2f}, requested: ₹{req_amount:.2f}"
            )

        new_balance = round(current_bal - req_amount, 2)
        card.current_balance = new_balance
        self.db.add(card)

        tx = GiftCardTransaction(
            gift_card_id=card.id,
            transaction_type=GiftCardTransactionType.REDEEM,
            amount=-req_amount,
            balance_after=new_balance,
            reference_order_id=data.reference_order_id,
            notes=f"Redeemed ₹{req_amount:.2f} at checkout",
        )
        self.db.add(tx)
        await self.db.flush()
        await self.db.refresh(card)
        return card

    async def list_gift_cards(
        self, business_id: UUID, is_active: Optional[bool] = None
    ) -> List[GiftCard]:
        q = select(GiftCard).where(
            GiftCard.business_id == business_id,
            GiftCard.deleted_at.is_(None),
        )
        if is_active is not None:
            q = q.where(GiftCard.is_active == is_active)
        q = q.order_by(GiftCard.created_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())
