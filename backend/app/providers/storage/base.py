"""
Storage provider interface.
All storage backends (local, S3-compatible) implement this.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class UploadResult:
    url: str                    # Public-accessible URL
    key: str                    # Storage key / path
    size_bytes: int
    content_type: str
    provider_data: dict


class StorageProvider(ABC):
    """Abstract file storage interface."""

    @abstractmethod
    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        public: bool = True,
    ) -> UploadResult:
        """Upload a file and return its public URL."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a file by key. Returns True on success."""
        ...

    @abstractmethod
    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a signed URL for private file access."""
        ...
