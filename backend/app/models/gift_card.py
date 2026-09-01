"""
Gift Card Models:
- GiftCard (digital gift card issued by salon with unique code and balance)
- GiftCardTransaction (history of purchases, redemptions, and top-ups)
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, SoftDeleteMixin


class GiftCardTransactionType(str, Enum):
    PURCHASE = "PURCHASE"
    REDEEM = "REDEEM"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


class GiftCard(SoftDeleteMixin, BaseModel):
    """Digital Gift Card issued by salon."""
    __tablename__ = "gift_cards"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    initial_balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    current_balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    recipient_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    recipient_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    purchaser_customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    transactions: Mapped[List["GiftCardTransaction"]] = relationship(
        back_populates="gift_card", cascade="all, delete-orphan", lazy="selectin"
    )


class GiftCardTransaction(SoftDeleteMixin, BaseModel):
    """Ledger transaction on a gift card."""
    __tablename__ = "gift_card_transactions"

    gift_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gift_cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[GiftCardTransactionType] = mapped_column(
        String(50), default=GiftCardTransactionType.REDEEM, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reference_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    gift_card: Mapped["GiftCard"] = relationship(back_populates="transactions", lazy="selectin")
