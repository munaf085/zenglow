"""
File upload endpoints — business logos, cover images, service photos, staff avatars.

Storage backend is configured via STORAGE_PROVIDER env var:
  local — saves to ./uploads/ (development)
  s3    — MinIO or S3-compatible (production)

All uploaded files are scoped with a structured key:
  businesses/{business_id}/logo/{uuid}.{ext}
  businesses/{business_id}/cover/{uuid}.{ext}
  businesses/{business_id}/services/{service_id}/{uuid}.{ext}
  staff/{business_id}/{staff_id}/{uuid}.{ext}
  customers/{customer_id}/avatar/{uuid}.{ext}
"""
import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, assert_business_access
from app.core.exceptions import StorageError, ValidationError
from app.db.session import get_db
from app.models.business import Business
from app.models.staff import Staff
from app.providers.storage.factory import get_storage_provider
from pydantic import BaseModel

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Allowed MIME types for image uploads
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}

# Extension map
MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


class UploadResponse(BaseModel):
    url: str
    key: str
    size_bytes: int
    content_type: str


def _validate_image(file: UploadFile, data: bytes) -> str:
    """Validate content type and size. Returns extension."""
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' is not supported. "
                   f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}",
        )
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {len(data):,} bytes exceeds maximum of {MAX_IMAGE_SIZE:,} bytes (10 MB)",
        )
    return MIME_TO_EXT.get(content_type, "jpg")


@router.post(
    "/business/{business_id}/logo",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_business_logo(
    business_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload business logo. Automatically updates business.logo_url."""
    assert_business_access(current_user, business_id)
    data = await file.read()
    ext = _validate_image(file, data)

    key = f"businesses/{business_id}/logo/{uuid.uuid4().hex}.{ext}"
    storage = get_storage_provider()

    try:
        result = await storage.upload(data, key, file.content_type or "image/jpeg")
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Update business record
    res = await db.execute(select(Business).where(Business.id == business_id))
    business = res.scalar_one_or_none()
    if business:
        # Delete old logo if it exists
        if business.logo_url and "/" in business.logo_url:
            old_key = business.logo_url.split("/", 3)[-1] if business.logo_url.startswith("http") else business.logo_url
            try:
                await storage.delete(old_key)
            except Exception:
                pass
        business.logo_url = result.url
        db.add(business)
        await db.flush()

    return UploadResponse(
        url=result.url,
        key=result.key,
        size_bytes=result.size_bytes,
        content_type=result.content_type,
    )


@router.post(
    "/business/{business_id}/cover",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_business_cover(
    business_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload business cover/banner image."""
    assert_business_access(current_user, business_id)
    data = await file.read()
    ext = _validate_image(file, data)

    key = f"businesses/{business_id}/cover/{uuid.uuid4().hex}.{ext}"
    storage = get_storage_provider()

    try:
        result = await storage.upload(data, key, file.content_type or "image/jpeg")
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))

    res = await db.execute(select(Business).where(Business.id == business_id))
    business = res.scalar_one_or_none()
    if business:
        business.cover_image_url = result.url
        db.add(business)
        await db.flush()

    return UploadResponse(
        url=result.url, key=result.key,
        size_bytes=result.size_bytes, content_type=result.content_type,
    )


@router.post(
    "/business/{business_id}/staff/{staff_id}/avatar",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_staff_avatar(
    business_id: UUID,
    staff_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload staff member avatar photo."""
    assert_business_access(current_user, business_id)
    data = await file.read()
    ext = _validate_image(file, data)

    key = f"staff/{business_id}/{staff_id}/{uuid.uuid4().hex}.{ext}"
    storage = get_storage_provider()

    try:
        result = await storage.upload(data, key, file.content_type or "image/jpeg")
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))

    res = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.business_id == business_id)
    )
    staff = res.scalar_one_or_none()
    if staff:
        staff.avatar_url = result.url
        db.add(staff)
        await db.flush()

    return UploadResponse(
        url=result.url, key=result.key,
        size_bytes=result.size_bytes, content_type=result.content_type,
    )


@router.post(
    "/business/{business_id}/service/{service_id}/image",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_service_image(
    business_id: UUID,
    service_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload service display image."""
    assert_business_access(current_user, business_id)
    data = await file.read()
    ext = _validate_image(file, data)

    key = f"businesses/{business_id}/services/{service_id}/{uuid.uuid4().hex}.{ext}"
    storage = get_storage_provider()

    try:
        result = await storage.upload(data, key, file.content_type or "image/jpeg")
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))

    from app.models.service import Service
    res = await db.execute(
        select(Service).where(Service.id == service_id, Service.business_id == business_id)
    )
    service = res.scalar_one_or_none()
    if service:
        service.image_url = result.url
        db.add(service)
        await db.flush()

    return UploadResponse(
        url=result.url, key=result.key,
        size_bytes=result.size_bytes, content_type=result.content_type,
    )


@router.delete("/object")
async def delete_object(
    key: str,
    current_user: CurrentUser = None,
):
    """Delete a stored object by key. Only usable by authenticated users."""
    storage = get_storage_provider()
    deleted = await storage.delete(key)
    return {"deleted": deleted, "key": key}
