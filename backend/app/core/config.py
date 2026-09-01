"""
Application configuration using Pydantic Settings.
All secrets come from environment variables — never hardcode.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "Zenglow API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_SECRET_KEY: str = "change-this-jwt-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Stored as plain string, parsed into list by property below
    ALLOWED_ORIGINS_STR: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    )

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:  # noqa: N802
        raw = self.ALLOWED_ORIGINS_STR.strip()
        if raw.startswith("["):
            import json
            try:
                return json.loads(raw)
            except Exception:
                pass
        return [o.strip() for o in raw.split(",") if o.strip()]

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://zenglow:zenglow_dev@localhost:5432/zenglow_db"
    DATABASE_TEST_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    SLOT_LOCK_TTL_SECONDS: int = 300  # 5 minutes

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Storage ───────────────────────────────────────────────────────────────
    STORAGE_PROVIDER: str = "local"  # local | s3
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "zenglow-media"
    S3_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = "./uploads"

    # ── Payments ─────────────────────────────────────────────────────────────
    PAYMENT_PROVIDER: str = "razorpay"  # razorpay | mock
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    # ── Email ─────────────────────────────────────────────────────────────────
    EMAIL_PROVIDER: str = "console"  # console | smtp | sendgrid
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@zenglow.com"
    EMAIL_FROM_NAME: str = "Zenglow"

    # ── SMS ───────────────────────────────────────────────────────────────────
    SMS_PROVIDER: str = "console"  # console | twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    WHATSAPP_PROVIDER: str = "console"  # console | twilio
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None
    TWILIO_WHATSAPP_FROM: Optional[str] = None  # e.g. whatsapp:+14155238886 (Twilio sandbox)

    # ── Push Notifications ────────────────────────────────────────────────────
    PUSH_PROVIDER: str = "console"
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None

    # ── Observability ─────────────────────────────────────────────────────────
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_SERVICE_NAME: str = "zenglow-api"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_test(self) -> bool:
        return self.ENVIRONMENT == "test"

    @property
    def effective_database_url(self) -> str:
        if self.is_test and self.DATABASE_TEST_URL:
            return self.DATABASE_TEST_URL
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
