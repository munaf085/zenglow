"""
S3-compatible storage provider.
Works with MinIO (on-prem), AWS S3, Cloudflare R2, Backblaze B2 — any S3-compatible API.

IMPORTANT: This project uses on-prem deployment.
Default storage backend is MinIO (docker-compose includes MinIO service).
Never hardcode AWS-specific endpoints.
"""
import mimetypes
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger
from app.providers.storage.base import StorageProvider, UploadResult

logger = get_logger(__name__)


class S3StorageProvider(StorageProvider):
    def __init__(self) -> None:
        self._client = None
        self._bucket = settings.S3_BUCKET_NAME

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config

                kwargs: dict = {
                    "aws_access_key_id": settings.S3_ACCESS_KEY_ID,
                    "aws_secret_access_key": settings.S3_SECRET_ACCESS_KEY,
                    "region_name": settings.S3_REGION,
                    "config": Config(signature_version="s3v4"),
                }
                if settings.S3_ENDPOINT_URL:
                    # MinIO or other on-prem S3-compatible storage
                    kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

                self._client = boto3.client("s3", **kwargs)

                # Ensure bucket exists (MinIO / local dev)
                self._ensure_bucket()

            except ImportError:
                raise StorageError("boto3 not installed. Run: pip install boto3")
            except Exception as e:
                raise StorageError(f"Failed to initialize S3 client: {e}")
        return self._client

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist (useful for MinIO dev setup)."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            try:
                if settings.S3_REGION and settings.S3_REGION != "us-east-1":
                    self._client.create_bucket(
                        Bucket=self._bucket,
                        CreateBucketConfiguration={"LocationConstraint": settings.S3_REGION},
                    )
                else:
                    self._client.create_bucket(Bucket=self._bucket)
                logger.info("s3_bucket_created", bucket=self._bucket)
            except Exception as e:
                logger.warning("s3_bucket_create_failed", bucket=self._bucket, error=str(e))

    async def upload(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
        public: bool = True,
    ) -> UploadResult:
        try:
            client = self._get_client()
            extra_args: dict = {"ContentType": content_type}

            # For MinIO/on-prem: ACL may not be supported — skip if endpoint is custom
            if not settings.S3_ENDPOINT_URL and public:
                extra_args["ACL"] = "public-read"

            client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=file_data,
                **extra_args,
            )

            url = self._build_url(key)
            logger.info("s3_upload_success", key=key, bucket=self._bucket, size=len(file_data))

            return UploadResult(
                url=url,
                key=key,
                size_bytes=len(file_data),
                content_type=content_type,
                provider_data={"bucket": self._bucket, "key": key, "url": url},
            )
        except StorageError:
            raise
        except Exception as e:
            logger.error("s3_upload_failed", key=key, error=str(e))
            raise StorageError(f"Upload failed: {e}")

    async def delete(self, key: str) -> bool:
        try:
            client = self._get_client()
            client.delete_object(Bucket=self._bucket, Key=key)
            logger.info("s3_delete_success", key=key)
            return True
        except Exception as e:
            logger.error("s3_delete_failed", key=key, error=str(e))
            return False

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        try:
            client = self._get_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            raise StorageError(f"Failed to generate signed URL: {e}")

    def _build_url(self, key: str) -> str:
        """Build public URL for an object."""
        if settings.S3_ENDPOINT_URL:
            # MinIO or other on-prem: endpoint_url/bucket/key
            endpoint = settings.S3_ENDPOINT_URL.rstrip("/")
            return f"{endpoint}/{self._bucket}/{key}"
        # AWS S3 standard URL
        return f"https://{self._bucket}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
