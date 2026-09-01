"""
FastAPI dependency injection — auth, RBAC, tenant context.
"""
from typing import Annotated, List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthenticationError, AuthorizationError, TenantIsolationError
from app.core.security import decode_access_token
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.user import Role, RoleEnum, User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


# ── Current User ─────────────────────────────────────────────────────────────


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> User:
    """
    Extract and validate JWT from Authorization header.
    Returns the authenticated User object.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token revocation via Redis (graceful if Redis is offline)
    try:
        import hashlib
        token_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        revoke_key = f"revoked:access:{token_hash}"
        if await redis.exists(revoke_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        raise
    except Exception:
        pass

    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Returns the current user or None (for public endpoints that optionally use auth)."""
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
    except Exception:
        return None


# ── RBAC ─────────────────────────────────────────────────────────────────────


def get_user_roles(user: User, business_id: Optional[UUID] = None) -> List[str]:
    """
    Get role names for a user, optionally scoped to a business.
    Platform-level roles (business_id=None) are always included.
    """
    roles = []
    for ur in user.user_roles:
        # Platform-wide role
        if ur.business_id is None:
            roles.append(ur.role.name)
        # Business-scoped role
        elif business_id and str(ur.business_id) == str(business_id):
            roles.append(ur.role.name)
    return roles


def require_roles(*required_roles: RoleEnum):
    """
    Dependency factory that enforces role membership.
    Usage: Depends(require_roles(RoleEnum.PLATFORM_ADMIN))
    """
    async def check(
        current_user: User = Depends(get_current_user),
        x_business_id: Optional[str] = Header(None),
    ) -> User:
        business_id = UUID(x_business_id) if x_business_id else None
        if current_user.is_superuser:
            return current_user
        user_role_names = get_user_roles(current_user, business_id)
        for role in required_roles:
            if role.value in user_role_names:
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required role(s): {[r.value for r in required_roles]}",
        )
    return check


def require_platform_admin():
    return require_roles(RoleEnum.PLATFORM_ADMIN)


def require_business_staff():
    """Any business-level role."""
    return require_roles(
        RoleEnum.BUSINESS_OWNER,
        RoleEnum.BUSINESS_MANAGER,
        RoleEnum.STAFF,
        RoleEnum.RECEPTIONIST,
    )


# ── Tenant Isolation ─────────────────────────────────────────────────────────


def assert_business_access(user: User, business_id: UUID) -> None:
    """
    Raise TenantIsolationError if the user does not have any role
    scoped to the given business AND is not a platform admin.
    """
    if user.is_superuser:
        return
    for ur in user.user_roles:
        # Platform admin bypasses tenant isolation
        if ur.business_id is None and ur.role.name == RoleEnum.PLATFORM_ADMIN.value:
            return
        if ur.business_id and str(ur.business_id) == str(business_id):
            return
    raise TenantIsolationError()
