"""
Domain exceptions with consistent structure.
All HTTP error responses use these exceptions.
"""
from typing import Any, Dict, Optional


class ZenglowException(Exception):
    """Base exception for all Zenglow domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class NotFoundError(ZenglowException):
    def __init__(self, resource: str, resource_id: Any = None) -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=detail, code="NOT_FOUND")
        self.resource = resource
        self.resource_id = resource_id


class ValidationError(ZenglowException):
    def __init__(self, message: str, field: Optional[str] = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class AuthenticationError(ZenglowException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(ZenglowException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class TenantIsolationError(ZenglowException):
    def __init__(self) -> None:
        super().__init__(
            message="Access to this resource is not permitted",
            code="TENANT_ISOLATION_ERROR",
        )


class ConflictError(ZenglowException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CONFLICT")


class BusinessRuleError(ZenglowException):
    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION") -> None:
        super().__init__(message=message, code=code)


class SlotUnavailableError(ZenglowException):
    def __init__(self, message: str = "The requested time slot is not available") -> None:
        super().__init__(message=message, code="SLOT_UNAVAILABLE")


class PaymentError(ZenglowException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="PAYMENT_ERROR")


class StorageError(ZenglowException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="STORAGE_ERROR")


class RateLimitError(ZenglowException):
    def __init__(self) -> None:
        super().__init__(message="Rate limit exceeded", code="RATE_LIMIT_EXCEEDED")
