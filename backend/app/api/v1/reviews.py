"""
Reviews endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.deps import CurrentUser
from app.core.exceptions import ConflictError, NotFoundError, TenantIsolationError
from app.db.session import get_db
from app.models.customer import Customer
from app.models.review import Review

router = APIRouter(tags=["reviews"])


class ReviewCreate(BaseModel):
    business_id: UUID
    appointment_id: Optional[UUID] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: UUID
    business_id: UUID
    customer_id: UUID
    appointment_id: Optional[UUID] = None
    rating: int
    comment: Optional[str] = None
    is_published: bool
    owner_reply: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewReplyRequest(BaseModel):
    reply: str = Field(min_length=1, max_length=2000)


@router.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(
    data: ReviewCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Customer submits a review for a business."""
    # Get customer profile
    c_result = await db.execute(
        select(Customer).where(Customer.user_id == current_user.id)
    )
    customer = c_result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer profile")

    # Check for duplicate review on same appointment
    if data.appointment_id:
        existing = (await db.execute(
            select(Review).where(
                Review.appointment_id == data.appointment_id,
                Review.customer_id == customer.id,
            )
        )).scalar_one_or_none()
        if existing:
            raise ConflictError("You have already reviewed this appointment")

    review = Review(
        business_id=data.business_id,
        customer_id=customer.id,
        appointment_id=data.appointment_id,
        rating=data.rating,
        comment=data.comment,
        is_published=True,
    )
    db.add(review)
    await db.flush()
    return review


@router.get("/businesses/{business_id}/reviews", response_model=List[ReviewResponse])
async def list_business_reviews(
    business_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Public listing of reviews for a business."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Review)
        .where(
            Review.business_id == business_id,
            Review.is_published.is_(True),
        )
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all())


@router.get("/businesses/{business_id}/reviews/stats")
async def get_review_stats(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return average rating and review count for a business."""
    result = await db.execute(
        select(
            func.avg(Review.rating).label("average"),
            func.count(Review.id).label("count"),
        ).where(
            Review.business_id == business_id,
            Review.is_published.is_(True),
        )
    )
    row = result.one()
    return {
        "average_rating": round(float(row.average or 0), 1),
        "total_reviews": row.count,
    }


@router.post(
    "/businesses/{business_id}/reviews/{review_id}/reply",
    response_model=ReviewResponse,
)
async def reply_to_review(
    business_id: UUID,
    review_id: UUID,
    data: ReviewReplyRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Business owner can reply to a review."""
    from app.core.deps import assert_business_access
    assert_business_access(current_user, business_id)

    result = await db.execute(
        select(Review).where(
            Review.id == review_id,
            Review.business_id == business_id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Review", review_id)

    review.owner_reply = data.reply
    db.add(review)
    await db.flush()
    return review
