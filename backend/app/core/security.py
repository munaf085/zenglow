"""
Security utilities: password hashing, JWT creation/verification.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ──────────────────────────────────────────────────────────────────


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ───────────────────────────────────────────────────────────────────────


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a long-lived JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    Raises jose.JWTError on failure.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode access token and assert type."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """Decode refresh token and assert type."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return payload
