"""
Generic base repository with common CRUD operations.
"""
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, id: UUID) -> Optional[ModelT]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_raise(self, id: UUID) -> ModelT:
        from app.core.exceptions import NotFoundError
        obj = await self.get(id)
        if not obj:
            raise NotFoundError(self.model.__tablename__, id)
        return obj

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: int = 20,
        order_by: Optional[Any] = None,
    ) -> Tuple[List[ModelT], int]:
        q = select(self.model)
        count_q = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                col = getattr(self.model, key, None)
                if col is not None and value is not None:
                    q = q.where(col == value)
                    count_q = count_q.where(col == value)

        # Exclude soft-deleted
        if hasattr(self.model, "deleted_at"):
            q = q.where(self.model.deleted_at.is_(None))
            count_q = count_q.where(self.model.deleted_at.is_(None))

        if order_by is not None:
            q = q.order_by(order_by)

        total_result = await self.db.execute(count_q)
        total = total_result.scalar_one()

        q = q.offset(offset).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelT, **kwargs: Any) -> ModelT:
        for key, value in kwargs.items():
            if value is not None or key in kwargs:
                setattr(obj, key, value)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelT) -> None:
        if hasattr(obj, "soft_delete"):
            obj.soft_delete()
            self.db.add(obj)
            await self.db.flush()
        else:
            await self.db.delete(obj)
            await self.db.flush()
