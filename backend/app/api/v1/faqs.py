"""
FAQ API endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, assert_business_access
from app.db.session import get_db
from app.schemas.faq import FAQCreate, FAQResponse
from app.services.faq_service import FAQService


router = APIRouter(
    prefix="/businesses/{business_id}/faqs",
    tags=["faqs"],
)


public_router = APIRouter(
    prefix="/businesses/public",
    tags=["faqs"],
)


def _svc(db: AsyncSession = Depends(get_db)) -> FAQService:
    return FAQService(db)


@router.post(
    "",
    response_model=FAQResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_faq(
    business_id: UUID,
    data: FAQCreate,
    current_user: CurrentUser,
    svc: FAQService = Depends(_svc),
):
    return await svc.create_faq(
        business_id,
        data,
        current_user,
    )


@router.get(
    "",
    response_model=List[FAQResponse],
)
async def list_faqs(
    business_id: UUID,
    current_user: CurrentUser,
    svc: FAQService = Depends(_svc),
):
    assert_business_access(current_user, business_id)
    return await svc.list_faqs(business_id)


@router.get(
    "/{faq_id}",
    response_model=FAQResponse,
)
async def get_faq(
    business_id: UUID,
    faq_id: UUID,
    current_user: CurrentUser,
    svc: FAQService = Depends(_svc),
):
    assert_business_access(current_user, business_id)
    return await svc.get_faq(
        business_id,
        faq_id,
    )


@public_router.get(
    "/{slug}/faqs",
    response_model=List[FAQResponse],
)
async def list_public_faqs(
    slug: str,
    svc: FAQService = Depends(_svc),
):
    return await svc.list_public_faqs(slug)