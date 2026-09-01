"""
Storage provider factory.
"""
from app.core.config import settings
from app.providers.storage.base import StorageProvider


def get_storage_provider() -> StorageProvider:
    provider = settings.STORAGE_PROVIDER.lower()
    if provider == "s3":
        from app.providers.storage.s3_provider import S3StorageProvider
        return S3StorageProvider()
    # Default: local filesystem
    from app.providers.storage.local_provider import LocalStorageProvider
    return LocalStorageProvider()
