"""
Business and Branch repositories.
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.business import Branch, Business, BusinessStatus
from app.repositories.base import BaseRepository


class BusinessRepository(BaseRepository[Business]):
    model = Business

    async def get(self, id: UUID) -> Optional[Business]:
        result = await self.db.execute(
            select(Business)
            .where(Business.id == id, Business.deleted_at.is_(None))
            .options(selectinload(Business.branches))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Business]:
        result = await self.db.execute(
            select(Business)
            .where(Business.slug == slug, Business.deleted_at.is_(None))
            .options(selectinload(Business.branches))
        )
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: UUID) -> List[Business]:
        result = await self.db.execute(
            select(Business)
            .where(Business.owner_id == owner_id, Business.deleted_at.is_(None))
            .options(selectinload(Business.branches))
        )
        return list(result.scalars().all())

    async def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        city: Optional[str] = None,
        is_active: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Business], int]:
        q = select(Business).where(Business.deleted_at.is_(None))
        count_q = select(func.count()).select_from(Business).where(Business.deleted_at.is_(None))

        if is_active:
            q = q.where(Business.status == BusinessStatus.ACTIVE)
            count_q = count_q.where(Business.status == BusinessStatus.ACTIVE)

        if query:
            like = f"%{query}%"
            q = q.where(or_(Business.name.ilike(like), Business.description.ilike(like)))
            count_q = count_q.where(
                or_(Business.name.ilike(like), Business.description.ilike(like))
            )

        if category:
            q = q.where(Business.category == category)
            count_q = count_q.where(Business.category == category)

        total_result = await self.db.execute(count_q)
        total = total_result.scalar_one()

        q = q.options(selectinload(Business.branches)).offset(offset).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def slug_exists(self, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        q = select(Business.id).where(Business.slug == slug)
        if exclude_id:
            q = q.where(Business.id != exclude_id)
        result = await self.db.execute(q)
        return result.scalar_one_or_none() is not None


class BranchRepository(BaseRepository[Branch]):
    model = Branch

    async def get_by_business(self, business_id: UUID) -> List[Branch]:
        result = await self.db.execute(
            select(Branch).where(
                Branch.business_id == business_id, Branch.deleted_at.is_(None)
            )
        )
        return list(result.scalars().all())

    async def get_primary(self, business_id: UUID) -> Optional[Branch]:
        result = await self.db.execute(
            select(Branch).where(
                Branch.business_id == business_id,
                Branch.is_primary.is_(True),
                Branch.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
