"""
Payment tests — verifies that payment verification is always server-side.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.staff import Staff, StaffService as StaffServiceModel, WorkingHours
from app.models.service import Service
from datetime import datetime, timedelta, timezone


async def _create_confirmed_booking(client, business, branch, db, roles):
    """Helper: create service, staff, and a confirmed appointment."""
    service = Service(
        business_id=business.id, name="Payment Test Svc",
        price=1000.0, tax_rate=18.0, duration_minutes=60,
        is_active=True, online_booking_enabled=True,
    )
    db.add(service)
    staff = Staff(
        business_id=business.id, branch_id=branch.id,
        first_name="Pay", last_name="Staff",
        status="ACTIVE", bookable=True,
    )
    db.add(staff)
    await db.flush()
    db.add(StaffServiceModel(staff_id=staff.id, service_id=service.id))
    for day in range(7):
        db.add(WorkingHours(
            entity_type="staff", entity_id=staff.id,
            business_id=business.id, day_of_week=day,
            is_open=True, open_time="08:00", close_time="22:00",
        ))
    await db.flush()
    return service, staff


@pytest.mark.asyncio
class TestPaymentFlow:
    async def test_create_payment_order(
        self, client: AsyncClient, business_with_owner, customer_user, db: AsyncSession, roles
    ):
        from tests.conftest import _make_user
        from app.models.user import RoleEnum

        business, branch, _, _ = business_with_owner
        service, staff = await _create_confirmed_booking(client, business, branch, db, roles)
        _, cust_token = customer_user

        start = (datetime.now(timezone.utc) + timedelta(days=3)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        booking = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{"service_id": str(service.id), "staff_id": str(staff.id), "start_time": start.isoformat()}],
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert booking.status_code == 201
        appointment_id = booking.json()["id"]

        # Create payment order
        res = await client.post(
            "/api/v1/payments/orders",
            json={"appointment_id": appointment_id, "amount": 1180.0, "currency": "INR"},
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert "provider_order_id" in data
        assert data["status"] == "PENDING"

    async def test_payment_verify_mock_provider(
        self, client: AsyncClient, business_with_owner, customer_user, db: AsyncSession, roles
    ):
        """Mock provider accepts payments with mock_ prefix."""
        business, branch, _, _ = business_with_owner
        service, staff = await _create_confirmed_booking(client, business, branch, db, roles)
        _, cust_token = customer_user

        start = (datetime.now(timezone.utc) + timedelta(days=4)).replace(
            hour=15, minute=0, second=0, microsecond=0
        )
        booking = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{"service_id": str(service.id), "staff_id": str(staff.id), "start_time": start.isoformat()}],
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        appointment_id = booking.json()["id"]

        order_res = await client.post(
            "/api/v1/payments/orders",
            json={"appointment_id": appointment_id, "amount": 1000.0},
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        payment_id = order_res.json()["payment_id"]
        provider_order_id = order_res.json()["provider_order_id"]

        # Verify with mock payment ID
        verify_res = await client.post(
            "/api/v1/payments/verify",
            json={
                "payment_id": payment_id,
                "provider_order_id": provider_order_id,
                "provider_payment_id": "mock_pay_12345",
                "provider_signature": "mock_sig",
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert verify_res.status_code == 200
        assert verify_res.json()["status"] == "CAPTURED"

    async def test_invalid_payment_signature_rejected(
        self, client: AsyncClient, business_with_owner, customer_user, db: AsyncSession, roles
    ):
        """Non-mock payment IDs should fail with mock provider (verify returns False)."""
        business, branch, _, _ = business_with_owner
        service, staff = await _create_confirmed_booking(client, business, branch, db, roles)
        _, cust_token = customer_user

        start = (datetime.now(timezone.utc) + timedelta(days=7)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        booking = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{"service_id": str(service.id), "staff_id": str(staff.id), "start_time": start.isoformat()}],
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        appointment_id = booking.json()["id"]
        order_res = await client.post(
            "/api/v1/payments/orders",
            json={"appointment_id": appointment_id, "amount": 1000.0},
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        payment_id = order_res.json()["payment_id"]
        provider_order_id = order_res.json()["provider_order_id"]

        # Provide a clearly non-mock payment ID — mock provider rejects it
        verify_res = await client.post(
            "/api/v1/payments/verify",
            json={
                "payment_id": payment_id,
                "provider_order_id": provider_order_id,
                "provider_payment_id": "rzp_real_fakeid_not_mock",
                "provider_signature": "bad_signature",
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        # Mock provider only accepts mock_ prefix — should fail
        assert verify_res.status_code == 402
