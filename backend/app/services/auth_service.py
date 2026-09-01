"""
AuthService — registration, login, token management, password reset.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import Role, RoleEnum, User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.redis = redis

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user and assign the CUSTOMER role."""
        # Check email uniqueness
        existing = await self.db.execute(
            select(User).where(User.email == data.email.lower())
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email '{data.email}' is already registered")

        user = User(
            email=data.email.lower(),
            phone=data.phone,
            hashed_password=hash_password(data.password),
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()  # get user.id

        # Assign CUSTOMER role
        customer_role = await self._get_role(RoleEnum.CUSTOMER)
        user_role = UserRole(user_id=user.id, role_id=customer_role.id, business_id=None)
        self.db.add(user_role)

        # Create customer profile
        from app.models.customer import Customer
        customer = Customer(user_id=user.id)
        self.db.add(customer)

        await self.db.flush()
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return token pair."""
        result = await self.db.execute(
            select(User)
            .where(User.email == data.email.lower(), User.deleted_at.is_(None))
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Validate refresh token and issue new token pair (rotation)."""
        try:
            payload = decode_refresh_token(refresh_token)
            user_id = payload.get("sub")
        except JWTError:
            raise AuthenticationError("Invalid refresh token")

        # Check revocation
        import hashlib
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        revoke_key = f"revoked:refresh:{token_hash}"
        if await self.redis.exists(revoke_key):
            raise AuthenticationError("Refresh token has been revoked")

        try:
            uid = UUID(str(user_id))
        except Exception:
            raise AuthenticationError("Invalid user ID in token")

        result = await self.db.execute(
            select(User)
            .where(User.id == uid, User.deleted_at.is_(None))
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Revoke old refresh token
        await self._revoke_refresh_token(refresh_token, payload)

        return await self._issue_tokens(user)

    async def logout(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Revoke current tokens."""
        import hashlib
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        access_key = f"revoked:access:{token_hash}"
        await self.redis.setex(
            access_key, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1"
        )
        if refresh_token:
            try:
                payload = decode_refresh_token(refresh_token)
                await self._revoke_refresh_token(refresh_token, payload)
            except JWTError:
                pass

    async def _issue_tokens(self, user: User) -> TokenResponse:
        role_names = [ur.role.name for ur in user.user_roles]
        extra = {"roles": role_names}

        access_token = create_access_token(str(user.id), extra_claims=extra)
        refresh_token = create_refresh_token(str(user.id))
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    async def _revoke_refresh_token(self, token: str, payload: dict) -> None:
        import hashlib
        from datetime import timezone
        exp = payload.get("exp", 0)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        ttl = max(exp - now_ts, 1)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        revoke_key = f"revoked:refresh:{token_hash}"
        await self.redis.setex(revoke_key, ttl, "1")

    async def _get_role(self, role_enum: RoleEnum) -> Role:
        result = await self.db.execute(select(Role).where(Role.name == role_enum.value))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=role_enum.value, description=role_enum.value, is_system=True)
            self.db.add(role)
            await self.db.flush()
        return role

    async def assign_business_role(
        self, user_id: UUID, role_enum: RoleEnum, business_id: UUID
    ) -> UserRole:
        """Assign a business-scoped role to a user."""
        role = await self._get_role(role_enum)
        user_role = UserRole(user_id=user_id, role_id=role.id, business_id=business_id)
        self.db.add(user_role)
        await self.db.flush()
        return user_role

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        self.db.add(user)
