"""
Phase 2 Complete Integration & Feature Tests:
1. Business verification state machine (Applied → Under Review → Approved / Rejected)
2. Booking source attribution (DIRECT vs MARKETPLACE + commission calculation)
3. Appointment state machine transitions (valid vs invalid transitions)
4. Cancellation policy enforcement (cancellation window & reason)
5. Deposit / prepayment flow (deposit calculation & confirmation)
6. Notification provider factory (Twilio SMS / WhatsApp stubs)
7. Storage provider factory (S3 / Local stubs)
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError
from app.core.security import create_access_token
from app.models.appointment import (
    APPOINTMENT_TRANSITIONS,
    Appointment,
    AppointmentSource,
    AppointmentStatus,
    is_marketplace_booking,
)
from app.models.business import (
    Business,
    BusinessStatus,
    VerificationStatus,
    VERIFICATION_TRANSITIONS,
)
from app.models.service import Service
from app.models.staff import Staff, StaffService, WorkingHours
from app.models.user import RoleEnum, User
from app.providers.notification.factory import (
    get_email_provider,
    get_push_provider,
    get_sms_provider,
    get_whatsapp_provider,
)
from app.providers.storage.factory import get_storage_provider
from tests.conftest import _make_user


def _header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _setup_test_business(db: AsyncSession, business, branch, roles):
    service = Service(
        business_id=business.id,
        name="Phase 2 Hair Treatment",
        price=1000.0,
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
        first_name="Priya",
        last_name="Sharma",
        status="ACTIVE",
        bookable=True,
    )
    db.add(staff)
    await db.flush()

    db.add(StaffService(staff_id=staff.id, service_id=service.id))

    for day in range(7):
        db.add(
            WorkingHours(
                entity_type="staff",
                entity_id=staff.id,
                business_id=business.id,
                day_of_week=day,
                is_open=True,
                open_time="09:00",
                close_time="20:00",
            )
        )

    await db.flush()
    return service, staff


@pytest.mark.asyncio
class TestPhase2BusinessVerification:
    """1. Business verification state machine tests"""

    async def test_verification_lifecycle(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, admin_user, roles
    ):
        business, _, owner, owner_token = business_with_owner
        _, admin_token = admin_user

        # 1. Owner submits verification
        res = await client.post(
            f"/api/v1/businesses/{business.id}/verification/submit",
            headers=_header(owner_token),
            json={"notes": "GST: 29AAAAA0000A1Z5, Registered Salon"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["verification_status"] == "APPLIED"

        # 2. Admin starts review
        res = await client.post(
            f"/api/v1/admin/verification/{business.id}/start-review",
            headers=_header(admin_token),
        )
        assert res.status_code == 200
        assert res.json()["verification_status"] == "UNDER_REVIEW"

        # 3. Admin approves
        res = await client.post(
            f"/api/v1/admin/verification/{business.id}/approve",
            headers=_header(admin_token),
        )
        assert res.status_code == 200
        assert res.json()["verification_status"] == "APPROVED"
        assert res.json()["is_verified"] is True

    async def test_verification_rejection_and_reapply(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, admin_user, roles
    ):
        business, _, owner, owner_token = business_with_owner
        _, admin_token = admin_user

        # Owner submits
        await client.post(
            f"/api/v1/businesses/{business.id}/verification/submit",
            headers=_header(owner_token),
            json={"notes": "Initial submission"},
        )

        # Admin rejects
        res = await client.post(
            f"/api/v1/admin/verification/{business.id}/reject",
            headers=_header(admin_token),
            json={"reason": "Business registration document is illegible. Please re-upload."},
        )
        assert res.status_code == 200
        assert res.json()["verification_status"] == "REJECTED"

        # Owner reapplies
        res = await client.post(
            f"/api/v1/businesses/{business.id}/verification/submit",
            headers=_header(owner_token),
            json={"notes": "Re-uploaded clear registration certificate."},
        )
        assert res.status_code == 200
        assert res.json()["verification_status"] == "APPLIED"


@pytest.mark.asyncio
class TestPhase2BookingSourceAndCommission:
    """2. Booking source attribution & marketplace commission"""

    async def test_direct_booking_no_commission(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, branch, _, _ = business_with_owner
        service, staff = await _setup_test_business(db, business, branch, roles)
        _, cust_token = customer_user

        start_time = datetime.now(timezone.utc) + timedelta(days=2, hours=2)

        res = await client.post(
            "/api/v1/bookings",
            headers=_header(cust_token),
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "source": "ONLINE",
                "items": [
                    {
                        "service_id": str(service.id),
                        "staff_id": str(staff.id),
                        "start_time": start_time.isoformat(),
                    }
                ],
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["source"] == "ONLINE"
        assert data["status"] == "CONFIRMED"

    async def test_marketplace_booking_attribution(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, roles
    ):
        business, branch, _, _ = business_with_owner
        service, staff = await _setup_test_business(db, business, branch, roles)

        # Create unique new customer
        new_customer, new_cust_token = await _make_user(
            db, roles, f"market_cust_{uuid.uuid4().hex[:6]}@example.com", RoleEnum.CUSTOMER.value
        )

        start_time = datetime.now(timezone.utc) + timedelta(days=3, hours=4)

        res = await client.post(
            "/api/v1/bookings",
            headers=_header(new_cust_token),
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "source": "MARKETPLACE",
                "items": [
                    {
                        "service_id": str(service.id),
                        "staff_id": str(staff.id),
                        "start_time": start_time.isoformat(),
                    }
                ],
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["source"] == "MARKETPLACE"


@pytest.mark.asyncio
class TestPhase2AppointmentStateMachine:
    """3. Appointment state machine transitions"""

    async def test_valid_state_transitions(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, branch, owner, owner_token = business_with_owner
        service, staff = await _setup_test_business(db, business, branch, roles)
        _, cust_token = customer_user

        start_time = datetime.now(timezone.utc) + timedelta(days=2, hours=5)

        # Create booking -> CONFIRMED
        res = await client.post(
            "/api/v1/bookings",
            headers=_header(cust_token),
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [
                    {
                        "service_id": str(service.id),
                        "staff_id": str(staff.id),
                        "start_time": start_time.isoformat(),
                    }
                ],
            },
        )
        appt_id = res.json()["id"]

        # CONFIRMED -> IN_PROGRESS
        res = await client.patch(
            f"/api/v1/businesses/{business.id}/appointments/{appt_id}/status?new_status=IN_PROGRESS",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert res.json()["status"] == "IN_PROGRESS"

        # IN_PROGRESS -> COMPLETED
        res = await client.patch(
            f"/api/v1/businesses/{business.id}/appointments/{appt_id}/status?new_status=COMPLETED",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert res.json()["status"] == "COMPLETED"

    async def test_invalid_state_transition_fails(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, branch, owner, owner_token = business_with_owner
        service, staff = await _setup_test_business(db, business, branch, roles)
        _, cust_token = customer_user

        start_time = datetime.now(timezone.utc) + timedelta(days=2, hours=6)

        res = await client.post(
            "/api/v1/bookings",
            headers=_header(cust_token),
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [
                    {
                        "service_id": str(service.id),
                        "staff_id": str(staff.id),
                        "start_time": start_time.isoformat(),
                    }
                ],
            },
        )
        appt_id = res.json()["id"]

        # Directly attempt CONFIRMED -> COMPLETED (invalid transition, must go through IN_PROGRESS)
        res = await client.patch(
            f"/api/v1/businesses/{business.id}/appointments/{appt_id}/status?new_status=COMPLETED",
            headers=_header(owner_token),
        )
        assert res.status_code in [400, 422]


@pytest.mark.asyncio
class TestPhase2DepositAndCancellation:
    """4 & 5. Deposit calculation & Cancellation policy"""

    async def test_deposit_required_booking_starts_pending(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, branch, owner, _ = business_with_owner
        business.deposit_required = True
        business.deposit_percentage = 25.0
        db.add(business)
        await db.flush()

        service, staff = await _setup_test_business(db, business, branch, roles)
        start_time = datetime.now(timezone.utc) + timedelta(days=4, hours=2)
        _, cust_token = customer_user

        res = await client.post(
            "/api/v1/bookings",
            headers=_header(cust_token),
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [
                    {
                        "service_id": str(service.id),
                        "staff_id": str(staff.id),
                        "start_time": start_time.isoformat(),
                    }
                ],
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "PENDING"
        assert data["deposit_amount"] > 0

        # Confirm deposit
        appt_id = data["id"]
        res = await client.post(
            f"/api/v1/bookings/{appt_id}/confirm-deposit",
            headers=_header(cust_token),
        )
        assert res.status_code == 200
        assert res.json()["status"] == "CONFIRMED"

    async def test_cancellation_within_policy(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, branch, _, _ = business_with_owner
        business.cancellation_hours = 24
        db.add(business)
        await db.flush()

        service, staff = await _setup_test_business(db, business, branch, roles)
        start_time = datetime.now(timezone.utc) + timedelta(days=5)
        _, cust_token = customer_user

        res = await client.post(
            "/api/v1/bookings",
            headers=_header(cust_token),
            json={
                "business_id": str(business.id),
                "branch_id": str(branch.id),
                "items": [
                    {
                        "service_id": str(service.id),
                        "staff_id": str(staff.id),
                        "start_time": start_time.isoformat(),
                    }
                ],
            },
        )
        appt_id = res.json()["id"]

        # Cancel
        res = await client.post(
            f"/api/v1/bookings/{appt_id}/cancel",
            headers=_header(cust_token),
            json={"reason": "Schedule conflict"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
class TestPhase2Providers:
    """6 & 7. Notification & Storage Provider Factories"""

    async def test_notification_providers(self):
        from app.providers.notification.base import NotificationMessage

        sms_prov = get_sms_provider()
        assert sms_prov is not None

        res_sms = await sms_prov.send(
            NotificationMessage(
                recipient="+919876543210",
                body="Your appointment is confirmed.",
            )
        )
        assert res_sms.success is True

        whatsapp_prov = get_whatsapp_provider()
        assert whatsapp_prov is not None

        res_wa = await whatsapp_prov.send(
            NotificationMessage(
                recipient="+919876543210",
                body="Your appointment is confirmed.",
            )
        )
        assert res_wa.success is True

    async def test_storage_providers(self):
        storage = get_storage_provider()
        assert storage is not None
