"""
Shared pytest fixtures for the entire test suite.
Uses a real PostgreSQL test database (configured via DATABASE_TEST_URL).
Each test function runs inside a rolled-back transaction for isolation.
"""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import Role, RoleEnum, User, UserRole

# ── Test database engine ──────────────────────────────────────────────────────
def _get_test_db_url() -> str:
    import os
    env_db = os.environ.get("DATABASE_URL", "")
    if "@postgres:" in env_db:
        base = env_db.rsplit("/", 1)[0]
        return f"{base}/zenglow_test".replace("postgresql://", "postgresql+asyncpg://")
    url = settings.DATABASE_TEST_URL or settings.DATABASE_URL
    return url.replace("postgresql://", "postgresql+asyncpg://")

TEST_DB_URL = _get_test_db_url()

test_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once per session; drop at end."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Per-test database session.
    Wraps each test in a SAVEPOINT so all changes are rolled back
    without resetting the schema.
    """
    async with test_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()  # SAVEPOINT
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with the test db injected."""
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Helper: seed roles ────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def roles(db: AsyncSession) -> dict[str, Role]:
    """Ensure all system roles exist and return a name→Role mapping."""
    role_map = {}
    for role_enum in RoleEnum:
        from sqlalchemy import select
        result = await db.execute(select(Role).where(Role.name == role_enum.value))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=role_enum.value, description=role_enum.value, is_system=True)
            db.add(role)
        role_map[role_enum.value] = role
    await db.flush()
    return role_map


# ── Helper: create user ───────────────────────────────────────────────────────
async def _make_user(
    db: AsyncSession,
    roles_map: dict,
    email: str,
    role_name: str,
    business_id=None,
    is_superuser: bool = False,
) -> tuple[User, str]:
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        hashed_password=hash_password("Test@1234"),
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()

    role = roles_map.get(role_name)
    if role:
        ur = UserRole(user_id=user.id, role_id=role.id, business_id=business_id)
        db.add(ur)
        await db.flush()

    from app.models.customer import Customer
    if role_name == RoleEnum.CUSTOMER.value:
        db.add(Customer(user_id=user.id))
        await db.flush()

    token = create_access_token(str(user.id), extra_claims={"roles": [role_name]})
    return user, token


@pytest_asyncio.fixture
async def customer_user(db: AsyncSession, roles: dict):
    return await _make_user(db, roles, f"customer_{uuid.uuid4().hex[:8]}@test.com", RoleEnum.CUSTOMER.value)


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession, roles: dict):
    return await _make_user(db, roles, f"admin_{uuid.uuid4().hex[:8]}@test.com", RoleEnum.PLATFORM_ADMIN.value, is_superuser=True)


@pytest_asyncio.fixture
async def business_with_owner(db: AsyncSession, roles: dict):
    """Create a business + branch + owner user. Returns (business, branch, owner, token)."""
    from app.models.business import Branch, Business, BusinessCategory, BusinessStatus
    from app.models.staff import WorkingHours

    owner, token = await _make_user(db, roles, f"owner_{uuid.uuid4().hex[:8]}@test.com", RoleEnum.CUSTOMER.value)

    business = Business(
        owner_id=owner.id,
        name="Test Salon",
        slug=f"test-salon-{uuid.uuid4().hex[:6]}",
        category=BusinessCategory.SALON,
        status=BusinessStatus.ACTIVE,
    )
    db.add(business)
    await db.flush()

    # Assign owner role scoped to business
    owner_role = roles[RoleEnum.BUSINESS_OWNER.value]
    db.add(UserRole(user_id=owner.id, role_id=owner_role.id, business_id=business.id))

    branch = Branch(
        business_id=business.id,
        name="Main Branch",
        is_primary=True,
        is_active=True,
        city="Mumbai",
    )
    db.add(branch)
    await db.flush()

    for day in range(7):
        db.add(WorkingHours(
            entity_type="branch", entity_id=branch.id,
            business_id=business.id, day_of_week=day,
            is_open=day < 6, open_time="09:00" if day < 6 else None,
            close_time="18:00" if day < 6 else None,
        ))

    await db.flush()
    new_token = create_access_token(str(owner.id), extra_claims={"roles": [RoleEnum.BUSINESS_OWNER.value]})
    return business, branch, owner, new_token
