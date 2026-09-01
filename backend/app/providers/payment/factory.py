"""
Payment provider factory — resolves the configured provider.
"""
from app.core.config import settings
from app.providers.payment.base import PaymentProvider


def get_payment_provider() -> PaymentProvider:
    """Return the configured payment provider."""
    provider = settings.PAYMENT_PROVIDER.lower()
    if provider == "razorpay":
        from app.providers.payment.razorpay_provider import RazorpayProvider
        return RazorpayProvider()
    elif provider in ("mock", "development"):
        from app.providers.payment.mock_provider import MockPaymentProvider
        return MockPaymentProvider()
    else:
        raise ValueError(f"Unknown payment provider: {provider}")
