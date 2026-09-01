"""
Authentication endpoints.
"""
from typing import Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.redis import get_redis
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> AuthService:
    return AuthService(db=db, redis=redis)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new customer account."""
    user = await service.register(data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Authenticate with email/password and receive JWT token pair."""
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Exchange a valid refresh token for a new token pair."""
    return await service.refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    data: RefreshRequest,
    current_user: CurrentUser = None,
    service: AuthService = Depends(get_auth_service),
):
    """Revoke current tokens (logout)."""
    auth_header = request.headers.get("authorization", "")
    access_token = auth_header.replace("Bearer ", "").replace("bearer ", "")
    await service.logout(access_token, data.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get the currently authenticated user's profile."""
    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    service: AuthService = Depends(get_auth_service),
):
    """Change the current user's password."""
    await service.change_password(current_user, data.current_password, data.new_password)
    return {"message": "Password changed successfully"}
