"""
BusinessService — business onboarding and management.
"""
import re
import unicodedata
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import assert_business_access
from app.core.exceptions import ConflictError, NotFoundError, TenantIsolationError
from app.core.logging import get_logger
from app.models.business import Branch, Business, BusinessStatus
from app.models.staff import WorkingHours
from app.models.user import RoleEnum, User
from app.repositories.business_repo import BranchRepository, BusinessRepository
from app.schemas.business import BranchCreate, BranchUpdate, BusinessCreate, BusinessUpdate
from app.services.auth_service import AuthService

logger = get_logger(__name__)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


class BusinessService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BusinessRepository(db)
        self.branch_repo = BranchRepository(db)

    async def create_business(
        self, owner: User, data: BusinessCreate, auth_service: AuthService
    ) -> Business:
        """Create a new business and assign BUSINESS_OWNER role to creator."""
        base_slug = slugify(data.name)
        slug = base_slug
        counter = 1
        while await self.repo.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Build default opening hours (Mon–Sat 09:00–18:00)
        business = Business(
            owner_id=owner.id,
            name=data.name,
            slug=slug,
            category=data.category,
            description=data.description,
            email=data.email,
            phone=data.phone,
            website=data.website,
            booking_advance_days=data.booking_advance_days,
            cancellation_hours=data.cancellation_hours,
            cancellation_policy=data.cancellation_policy,
            deposit_required=data.deposit_required,
            deposit_percentage=data.deposit_percentage,
            status=BusinessStatus.ACTIVE,
        )
        self.db.add(business)
        await self.db.flush()

        # Create primary branch
        branch_data = data.branch or BranchCreate(name="Main Branch", is_primary=True)
        branch = Branch(
            business_id=business.id,
            name=branch_data.name,
            is_primary=True,
            is_active=True,
            address_line1=branch_data.address_line1,
            city=branch_data.city,
            state=branch_data.state,
            country=branch_data.country,
            postal_code=branch_data.postal_code,
            phone=branch_data.phone,
            email=branch_data.email,
        )
        self.db.add(branch)
        await self.db.flush()

        # Default branch working hours (Mon–Sat 09:00–18:00, Sunday closed)
        for day in range(7):
            wh = WorkingHours(
                entity_type="branch",
                entity_id=branch.id,
                business_id=business.id,
                day_of_week=day,
                is_open=day < 6,
                open_time="09:00" if day < 6 else None,
                close_time="18:00" if day < 6 else None,
            )
            self.db.add(wh)

        # Assign BUSINESS_OWNER role
        await auth_service.assign_business_role(owner.id, RoleEnum.BUSINESS_OWNER, business.id)

        await self.db.flush()
        await self.db.refresh(business, ["branches"])
        logger.info("business_created", business_id=str(business.id), owner_id=str(owner.id))
        return business

    async def get_business(self, business_id: UUID, user: User) -> Business:
        business = await self.repo.get_or_raise(business_id)
        assert_business_access(user, business_id)
        return business

    async def get_public_business(self, slug_or_id: str) -> Business:
        """Public endpoint — only return ACTIVE businesses."""
        try:
            uid = UUID(slug_or_id)
            business = await self.repo.get_or_raise(uid)
        except ValueError:
            business = await self.repo.get_by_slug(slug_or_id)
            if not business:
                raise NotFoundError("Business", slug_or_id)

        if business.status != BusinessStatus.ACTIVE:
            raise NotFoundError("Business", slug_or_id)
        return business

    async def update_business(
        self, business_id: UUID, data: BusinessUpdate, user: User
    ) -> Business:
        business = await self.repo.get_or_raise(business_id)
        assert_business_access(user, business_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(business, key, value)

        self.db.add(business)
        await self.db.flush()
        await self.db.refresh(business, ["branches"])
        return business

    async def list_my_businesses(self, owner: User) -> List[Business]:
        return await self.repo.get_by_owner(owner.id)

    async def search_businesses(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        city: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Business], int]:
        return await self.repo.search(
            query=query, category=category, city=city,
            is_active=True, offset=offset, limit=limit
        )

    # ── Branches ─────────────────────────────────────────────────────────────

    async def create_branch(
        self, business_id: UUID, data: BranchCreate, user: User
    ) -> Branch:
        assert_business_access(user, business_id)
        await self.repo.get_or_raise(business_id)

        branch = Branch(
            business_id=business_id,
            **data.model_dump(),
        )
        self.db.add(branch)
        await self.db.flush()

        # Default working hours
        for day in range(7):
            wh = WorkingHours(
                entity_type="branch",
                entity_id=branch.id,
                business_id=business_id,
                day_of_week=day,
                is_open=day < 6,
                open_time="09:00" if day < 6 else None,
                close_time="18:00" if day < 6 else None,
            )
            self.db.add(wh)

        return branch

    async def update_branch(
        self, business_id: UUID, branch_id: UUID, data: BranchUpdate, user: User
    ) -> Branch:
        assert_business_access(user, business_id)
        branch = await self.branch_repo.get_or_raise(branch_id)
        if str(branch.business_id) != str(business_id):
            raise TenantIsolationError()

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(branch, key, value)

        self.db.add(branch)
        await self.db.flush()
        return branch

    async def list_branches(self, business_id: UUID, user: User) -> List[Branch]:
        assert_business_access(user, business_id)
        return await self.branch_repo.get_by_business(business_id)
