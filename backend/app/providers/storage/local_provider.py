"""
Local filesystem storage provider — for development only.
Files are saved to LOCAL_STORAGE_PATH and served statically.
"""
import hashlib
import os
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger
from app.providers.storage.base import StorageProvider, UploadResult

logger = get_logger(__name__)


class LocalStorageProvider(StorageProvider):
    def __init__(self) -> None:
        self.base_path = Path(settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        public: bool = True,
    ) -> UploadResult:
        try:
            file_path = self.base_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(file_data)

            # Build a URL that the dev server can serve
            api_base = f"http://localhost:{settings.__dict__.get('BACKEND_PORT', 8000)}"
            url = f"{api_base}/uploads/{key}"

            logger.info("local_storage_upload", key=key, size=len(file_data))
            return UploadResult(
                url=url,
                key=key,
                size_bytes=len(file_data),
                content_type=content_type,
                provider_data={"path": str(file_path)},
            )
        except Exception as e:
            raise StorageError(f"Local storage upload failed: {e}")

    async def delete(self, key: str) -> bool:
        try:
            file_path = self.base_path / key
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error("local_storage_delete_failed", key=key, error=str(e))
            return False

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        # Local dev — just return the direct URL
        api_base = f"http://localhost:8000"
        return f"{api_base}/uploads/{key}"
