"""
User profile management endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    data: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(current_user, k, v)
    db.add(current_user)
    await db.flush()
    return current_user
