"""
BusinessVerificationService — enforces the verification state machine.

State machine:
  NOT_APPLIED → APPLIED        (owner submits application)
  APPLIED → UNDER_REVIEW       (admin starts review)
  APPLIED → REJECTED           (admin fast-rejects, e.g. spam)
  UNDER_REVIEW → APPROVED      (admin approves — sets is_verified=True, status=ACTIVE)
  UNDER_REVIEW → REJECTED      (admin rejects with reason)
  REJECTED → APPLIED           (owner reapplies after fixing issues)

No other transitions are permitted. Any attempt raises BusinessRuleError.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.logging import get_logger
from app.models.business import (
    Business,
    BusinessStatus,
    VERIFICATION_TRANSITIONS,
    VerificationStatus,
)
from app.models.user import User

logger = get_logger(__name__)


class VerificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Owner actions ─────────────────────────────────────────────────────────

    async def submit_for_verification(
        self, business_id: UUID, owner: User, notes: Optional[str] = None
    ) -> Business:
        """
        Owner submits their business for verification.
        Allowed from: NOT_APPLIED, REJECTED
        """
        business = await self._get(business_id)
        self._check_owner(business, owner)

        self._assert_transition(
            business.verification_status, VerificationStatus.APPLIED
        )

        business.verification_status = VerificationStatus.APPLIED
        business.verification_submitted_at = datetime.now(timezone.utc)
        business.verification_rejection_reason = None  # clear previous rejection
        if notes:
            business.verification_notes = notes

        self.db.add(business)
        await self.db.flush()
        logger.info(
            "verification_submitted",
            business_id=str(business_id),
            owner_id=str(owner.id),
        )
        return business

    # ── Admin actions ─────────────────────────────────────────────────────────

    async def start_review(self, business_id: UUID, admin: User) -> Business:
        """Admin picks up the application for review. APPLIED → UNDER_REVIEW."""
        business = await self._get(business_id)
        self._assert_transition(
            business.verification_status, VerificationStatus.UNDER_REVIEW
        )

        business.verification_status = VerificationStatus.UNDER_REVIEW
        self.db.add(business)
        await self.db.flush()
        logger.info("verification_review_started", business_id=str(business_id))
        return business

    async def approve(self, business_id: UUID, admin: User) -> Business:
        """
        Admin approves the business.
        UNDER_REVIEW → APPROVED
        Side effects:
          - is_verified = True
          - status = ACTIVE (business can now receive bookings)
        """
        business = await self._get(business_id)
        self._assert_transition(
            business.verification_status, VerificationStatus.APPROVED
        )

        business.verification_status = VerificationStatus.APPROVED
        business.is_verified = True
        business.status = BusinessStatus.ACTIVE
        business.verification_reviewed_at = datetime.now(timezone.utc)
        business.verification_reviewed_by_id = admin.id
        business.verification_rejection_reason = None

        self.db.add(business)
        await self.db.flush()
        logger.info(
            "verification_approved",
            business_id=str(business_id),
            admin_id=str(admin.id),
        )
        return business

    async def reject(
        self, business_id: UUID, admin: User, reason: str
    ) -> Business:
        """
        Admin rejects the business with a mandatory reason.
        APPLIED | UNDER_REVIEW → REJECTED
        Side effects:
          - is_verified = False
          - status remains PENDING (not yet active)
        """
        if not reason or not reason.strip():
            raise BusinessRuleError("A rejection reason is required")

        business = await self._get(business_id)
        self._assert_transition(
            business.verification_status, VerificationStatus.REJECTED
        )

        business.verification_status = VerificationStatus.REJECTED
        business.is_verified = False
        business.verification_reviewed_at = datetime.now(timezone.utc)
        business.verification_reviewed_by_id = admin.id
        business.verification_rejection_reason = reason.strip()

        self.db.add(business)
        await self.db.flush()
        logger.info(
            "verification_rejected",
            business_id=str(business_id),
            admin_id=str(admin.id),
            reason=reason,
        )
        return business

    # ── Queries ───────────────────────────────────────────────────────────────

    async def list_pending_applications(self) -> list[Business]:
        """Return all businesses in APPLIED or UNDER_REVIEW state."""
        result = await self.db.execute(
            select(Business)
            .where(
                Business.verification_status.in_([
                    VerificationStatus.APPLIED,
                    VerificationStatus.UNDER_REVIEW,
                ]),
                Business.deleted_at.is_(None),
            )
            .order_by(Business.verification_submitted_at)
        )
        return list(result.scalars().all())

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get(self, business_id: UUID) -> Business:
        result = await self.db.execute(
            select(Business).where(
                Business.id == business_id,
                Business.deleted_at.is_(None),
            )
        )
        business = result.scalar_one_or_none()
        if not business:
            raise NotFoundError("Business", business_id)
        return business

    def _check_owner(self, business: Business, user: User) -> None:
        if str(business.owner_id) != str(user.id) and not user.is_superuser:
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError("Only the business owner can submit for verification")

    @staticmethod
    def _assert_transition(
        current: VerificationStatus, target: VerificationStatus
    ) -> None:
        allowed = VERIFICATION_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise BusinessRuleError(
                f"Cannot transition from {current} to {target}. "
                f"Allowed transitions: {allowed or 'none (terminal state)'}"
            )
