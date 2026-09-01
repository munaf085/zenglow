"""
Booking engine tests:
- Availability calculation
- Booking creation
- Double-booking prevention
- Cancellation
- Tenant isolation on bookings
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentItem, AppointmentStatus
from app.models.service import Service
from app.models.staff import Staff, StaffService as StaffServiceModel, WorkingHours


async def _setup_bookable_business(db: AsyncSession, business, branch, roles):
    """Add a service and bookable staff member to a business."""
    from tests.conftest import _make_user
    from app.models.user import RoleEnum

    service = Service(
        business_id=business.id,
        name="Test Haircut",
        price=500.0,
        tax_rate=18.0,
        duration_minutes=60,
        buffer_after_minutes=15,
        is_active=True,
        online_booking_enabled=True,
    )
    db.add(service)
    await db.flush()

    staff = Staff(
        business_id=business.id,
        branch_id=branch.id,
        first_name="Test",
        last_name="Stylist",
        status="ACTIVE",
        bookable=True,
    )
    db.add(staff)
    await db.flush()

    db.add(StaffServiceModel(staff_id=staff.id, service_id=service.id))

    for day in range(7):
        db.add(WorkingHours(
            entity_type="staff",
            entity_id=staff.id,
            business_id=business.id,
            day_of_week=day,
            is_open=True,
            open_time="08:00",
            close_time="22:00",
        ))

    await db.flush()
    return service, staff


@pytest.mark.asyncio
class TestAvailability:
    async def test_availability_returns_slots(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles
    ):
        business, branch, _, _ = business_with_owner
        service, _ = await _setup_bookable_business(db, business, branch, roles)

        # Pick next Monday
        today = datetime.now(timezone.utc)
        days_until_monday = (7 - today.weekday()) % 7 or 7
        target = today + timedelta(days=days_until_monday)

        res = await client.get(
            "/api/v1/availability",
            params={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "service_id": str(service.id),
                "date": target.strftime("%Y-%m-%d"),
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["service_id"] == str(service.id)
        assert "slots" in data
        assert len(data["slots"]) > 0

    async def test_availability_no_slots_for_closed_day(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles
    ):
        """Sunday is closed — should return 0 slots (default branch hours)."""
        from sqlalchemy import update
        from app.models.staff import WorkingHours as WH

        business, branch, _, _ = business_with_owner
        service, staff = await _setup_bookable_business(db, business, branch, roles)

        # Mark all staff hours as closed
        await db.execute(
            update(WH)
            .where(WH.entity_type == "staff", WH.entity_id == staff.id)
            .values(is_open=False)
        )
        # Also close branch
        await db.execute(
            update(WH)
            .where(WH.entity_type == "branch", WH.entity_id == branch.id)
            .values(is_open=False)
        )
        await db.flush()

        res = await client.get(
            "/api/v1/availability",
            params={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "service_id": str(service.id),
                "date": (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d"),
            },
        )
        assert res.status_code == 200
        assert res.json()["slots"] == []


@pytest.mark.asyncio
class TestBookingCreation:
    async def test_create_booking_success(
        self, client: AsyncClient, business_with_owner, customer_user, db: AsyncSession, roles
    ):
        business, branch, _, _ = business_with_owner
        service, staff = await _setup_bookable_business(db, business, branch, roles)
        _, cust_token = customer_user

        # Book 3 days from now at 10am
        start = (datetime.now(timezone.utc) + timedelta(days=3)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        res = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{
                    "service_id": str(service.id),
                    "staff_id": str(staff.id),
                    "start_time": start.isoformat(),
                }],
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "CONFIRMED"
        assert data["business_id"] == str(business.id)
        assert len(data["items"]) == 1
        assert data["items"][0]["service_name"] == "Test Haircut"
        assert float(data["subtotal"]) == 500.0

    async def test_create_booking_requires_auth(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles
    ):
        business, branch, _, _ = business_with_owner
        service, staff = await _setup_bookable_business(db, business, branch, roles)

        res = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{"service_id": str(service.id), "start_time": datetime.now(timezone.utc).isoformat()}],
            },
        )
        assert res.status_code == 401

    async def test_cannot_book_in_past(
        self, client: AsyncClient, business_with_owner, customer_user, db: AsyncSession, roles
    ):
        business, branch, _, _ = business_with_owner
        service, staff = await _setup_bookable_business(db, business, branch, roles)
        _, cust_token = customer_user

        past = datetime.now(timezone.utc) - timedelta(hours=2)

        res = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{"service_id": str(service.id), "staff_id": str(staff.id), "start_time": past.isoformat()}],
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert res.status_code in (400, 409)


@pytest.mark.asyncio
class TestDoubleBookingPrevention:
    async def test_double_booking_rejected(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles
    ):
        """
        Two concurrent bookings for the same staff at the same time should result
        in exactly one success and one conflict.
        """
        from tests.conftest import _make_user
        from app.models.user import RoleEnum

        business, branch, _, _ = business_with_owner
        service, staff = await _setup_bookable_business(db, business, branch, roles)

        # Create two separate customer users
        _, token1 = await _make_user(db, roles, f"cust_dbl1_{uuid.uuid4().hex[:6]}@test.com", RoleEnum.CUSTOMER.value)
        _, token2 = await _make_user(db, roles, f"cust_dbl2_{uuid.uuid4().hex[:6]}@test.com", RoleEnum.CUSTOMER.value)

        start = (datetime.now(timezone.utc) + timedelta(days=5)).replace(
            hour=14, minute=0, second=0, microsecond=0
        )
        payload = {
            "business_id": str(business.id),
            "branch_id": str(branch.id),
            "items": [{"service_id": str(service.id), "staff_id": str(staff.id), "start_time": start.isoformat()}],
        }

        # First booking should succeed
        res1 = await client.post("/api/v1/bookings", json=payload, headers={"Authorization": f"Bearer {token1}"})
        assert res1.status_code == 201

        # Second booking at same time should fail
        res2 = await client.post("/api/v1/bookings", json=payload, headers={"Authorization": f"Bearer {token2}"})
        assert res2.status_code == 409


@pytest.mark.asyncio
class TestBookingManagement:
    async def test_cancel_booking(
        self, client: AsyncClient, business_with_owner, customer_user, db: AsyncSession, roles
    ):
        business, branch, _, _ = business_with_owner
        service, staff = await _setup_bookable_business(db, business, branch, roles)
        _, cust_token = customer_user

        start = (datetime.now(timezone.utc) + timedelta(days=4)).replace(
            hour=11, minute=0, second=0, microsecond=0
        )
        booking_res = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{"service_id": str(service.id), "staff_id": str(staff.id), "start_time": start.isoformat()}],
            },
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert booking_res.status_code == 201
        appointment_id = booking_res.json()["id"]

        cancel_res = await client.post(
            f"/api/v1/bookings/{appointment_id}/cancel",
            json={"reason": "Change of plans"},
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

    async def test_list_my_bookings(
        self, client: AsyncClient, customer_user
    ):
        _, cust_token = customer_user
        res = await client.get(
            "/api/v1/bookings/me",
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_customer_cannot_see_other_customers_booking(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles
    ):
        from tests.conftest import _make_user
        from app.models.user import RoleEnum

        business, branch, _, _ = business_with_owner
        service, staff = await _setup_bookable_business(db, business, branch, roles)

        _, token1 = await _make_user(db, roles, f"ciso1_{uuid.uuid4().hex[:6]}@test.com", RoleEnum.CUSTOMER.value)
        _, token2 = await _make_user(db, roles, f"ciso2_{uuid.uuid4().hex[:6]}@test.com", RoleEnum.CUSTOMER.value)

        start = (datetime.now(timezone.utc) + timedelta(days=6)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        booking_res = await client.post(
            "/api/v1/bookings",
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [{"service_id": str(service.id), "staff_id": str(staff.id), "start_time": start.isoformat()}],
            },
            headers={"Authorization": f"Bearer {token1}"},
        )
        appointment_id = booking_res.json()["id"]

        # Customer 2 should NOT be able to fetch customer 1's booking
        res = await client.get(
            f"/api/v1/bookings/{appointment_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert res.status_code == 404
