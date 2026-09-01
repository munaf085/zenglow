"""
Business verification endpoints.

Owner routes:
  POST /businesses/{id}/verification/submit  — owner submits for review
  GET  /businesses/{id}/verification/status  — owner checks their status

Admin routes (require PLATFORM_ADMIN):
  GET  /admin/verification/queue             — list pending applications
  POST /admin/verification/{id}/start-review
  POST /admin/verification/{id}/approve
  POST /admin/verification/{id}/reject
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_platform_admin
from app.db.session import get_db
from app.models.business import VerificationStatus
from app.services.verification_service import VerificationService
from datetime import datetime

router = APIRouter(tags=["verification"])


# ── Schemas ────────────────────────────────────────────────────────────────────


class VerificationStatusResponse(BaseModel):
    business_id: UUID
    verification_status: VerificationStatus
    is_verified: bool
    verification_submitted_at: Optional[datetime] = None
    verification_reviewed_at: Optional[datetime] = None
    verification_rejection_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class SubmitVerificationRequest(BaseModel):
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes from the owner (e.g. business license info)",
    )


class RejectVerificationRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=1000)


# ── Owner endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/businesses/{business_id}/verification/submit",
    response_model=VerificationStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_for_verification(
    business_id: UUID,
    data: SubmitVerificationRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Owner submits their business for platform verification.
    Allowed when status is NOT_APPLIED or REJECTED (reapplication).
    """
    svc = VerificationService(db)
    business = await svc.submit_for_verification(business_id, current_user, data.notes)
    return VerificationStatusResponse(
        business_id=business.id,
        verification_status=business.verification_status,
        is_verified=business.is_verified,
        verification_submitted_at=business.verification_submitted_at,
        verification_reviewed_at=business.verification_reviewed_at,
        verification_rejection_reason=business.verification_rejection_reason,
    )


@router.get(
    "/businesses/{business_id}/verification/status",
    response_model=VerificationStatusResponse,
)
async def get_verification_status(
    business_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Owner checks current verification status of their business."""
    from app.core.deps import assert_business_access
    assert_business_access(current_user, business_id)

    from sqlalchemy import select
    from app.models.business import Business
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Business", business_id)

    return VerificationStatusResponse(
        business_id=business.id,
        verification_status=business.verification_status,
        is_verified=business.is_verified,
        verification_submitted_at=business.verification_submitted_at,
        verification_reviewed_at=business.verification_reviewed_at,
        verification_rejection_reason=business.verification_rejection_reason,
    )


# ── Admin endpoints ────────────────────────────────────────────────────────────


@router.get(
    "/admin/verification/queue",
    response_model=List[dict],
    dependencies=[Depends(require_platform_admin())],
)
async def get_verification_queue(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin: list all businesses pending verification (APPLIED or UNDER_REVIEW)."""
    svc = VerificationService(db)
    businesses = await svc.list_pending_applications()
    return [
        {
            "id": str(b.id),
            "name": b.name,
            "category": b.category,
            "owner_id": str(b.owner_id),
            "verification_status": b.verification_status,
            "verification_submitted_at": (
                b.verification_submitted_at.isoformat()
                if b.verification_submitted_at
                else None
            ),
            "verification_notes": b.verification_notes,
        }
        for b in businesses
    ]


@router.post(
    "/admin/verification/{business_id}/start-review",
    response_model=VerificationStatusResponse,
    dependencies=[Depends(require_platform_admin())],
)
async def start_review(
    business_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin: move application to UNDER_REVIEW."""
    svc = VerificationService(db)
    business = await svc.start_review(business_id, current_user)
    return VerificationStatusResponse(
        business_id=business.id,
        verification_status=business.verification_status,
        is_verified=business.is_verified,
        verification_submitted_at=business.verification_submitted_at,
        verification_reviewed_at=business.verification_reviewed_at,
        verification_rejection_reason=business.verification_rejection_reason,
    )


@router.post(
    "/admin/verification/{business_id}/approve",
    response_model=VerificationStatusResponse,
    dependencies=[Depends(require_platform_admin())],
)
async def approve_business(
    business_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: approve business verification.
    Side effects: is_verified=True, status=ACTIVE.
    """
    svc = VerificationService(db)
    business = await svc.approve(business_id, current_user)
    return VerificationStatusResponse(
        business_id=business.id,
        verification_status=business.verification_status,
        is_verified=business.is_verified,
        verification_submitted_at=business.verification_submitted_at,
        verification_reviewed_at=business.verification_reviewed_at,
        verification_rejection_reason=business.verification_rejection_reason,
    )


@router.post(
    "/admin/verification/{business_id}/reject",
    response_model=VerificationStatusResponse,
    dependencies=[Depends(require_platform_admin())],
)
async def reject_business(
    business_id: UUID,
    data: RejectVerificationRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin: reject business verification with a mandatory reason.
    The owner will see the rejection reason and can reapply.
    """
    svc = VerificationService(db)
    business = await svc.reject(business_id, current_user, data.reason)
    return VerificationStatusResponse(
        business_id=business.id,
        verification_status=business.verification_status,
        is_verified=business.is_verified,
        verification_submitted_at=business.verification_submitted_at,
        verification_reviewed_at=business.verification_reviewed_at,
        verification_rejection_reason=business.verification_rejection_reason,
    )
