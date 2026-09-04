"""
FAQ service — business FAQ CRUD.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import assert_business_access
from app.core.exceptions import NotFoundError
from app.models.business import Business, BusinessStatus
from app.models.faq import FAQ
from app.models.user import User
from app.schemas.faq import FAQCreate


class FAQService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_faq(
        self,
        business_id: UUID,
        data: FAQCreate,
        user: User,
    ) -> FAQ:
        assert_business_access(user, business_id)

        faq = FAQ(
            business_id=business_id,
            question=data.question,
            answer=data.answer,
        )

        self.db.add(faq)
        await self.db.flush()

        return faq

    async def list_faqs(
        self,
        business_id: UUID,
    ) -> List[FAQ]:
        result = await self.db.execute(
            select(FAQ)
            .where(FAQ.business_id == business_id)
            .order_by(FAQ.created_at.asc())
        )

        return list(result.scalars().all())

    async def get_faq(
        self,
        business_id: UUID,
        faq_id: UUID,
    ) -> FAQ:
        result = await self.db.execute(
            select(FAQ).where(
                FAQ.id == faq_id,
                FAQ.business_id == business_id,
            )
        )

        faq = result.scalar_one_or_none()

        if not faq:
            raise NotFoundError("FAQ", faq_id)

        return faq

    async def list_public_faqs(
        self,
        slug: str,
    ) -> List[FAQ]:
        business_result = await self.db.execute(
            select(Business).where(
                Business.slug == slug,
                Business.status == BusinessStatus.ACTIVE,
                Business.deleted_at.is_(None),
            )
        )

        business = business_result.scalar_one_or_none()

        if not business:
            raise NotFoundError("Business", slug)

        faq_result = await self.db.execute(
            select(FAQ)
            .where(FAQ.business_id == business.id)
            .order_by(FAQ.created_at.asc())
        )

        return list(faq_result.scalars().all())