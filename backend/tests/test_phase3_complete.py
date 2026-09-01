"""
Phase 3 Complete Integration & Feature Tests:
1. Inventory Management (categories, products, stock movements, low stock alerts)
2. Memberships (plans, customer enrollments, active membership checks)
3. Packages (bundled templates, selling packages, session redemptions)
4. Gift Cards (issuance, code lookups, balance checks, redemptions)
5. POS Checkout (cart calculations, inventory stock decs, split tenders, invoices)
6. Reports & Analytics (revenue report, staff performance, inventory valuations, operations stats)
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.service import Service
from app.models.staff import Staff, StaffService, WorkingHours
from app.models.user import RoleEnum, User
from tests.conftest import _make_user


def _header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _setup_phase3_business(db: AsyncSession, business, branch, roles):
    service = Service(
        business_id=business.id,
        name="Phase 3 Spa Deluxe",
        price=1500.0,
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
        first_name="Rohan",
        last_name="Verma",
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
class TestPhase3Inventory:
    """1. Inventory Management Tests"""

    async def test_inventory_full_lifecycle(
        self, client: AsyncClient, db: AsyncSession, business_with_owner
    ):
        business, branch, owner, owner_token = business_with_owner

        # 1. Create Category
        res = await client.post(
            f"/api/v1/businesses/{business.id}/inventory/categories",
            headers=_header(owner_token),
            json={"name": "Hair Care", "description": "Shampoos and Serums"},
        )
        assert res.status_code == 201
        cat_id = res.json()["id"]

        # 2. Create Product
        res = await client.post(
            f"/api/v1/businesses/{business.id}/inventory/products",
            headers=_header(owner_token),
            json={
                "name": "Moroccan Argan Oil Serum",
                "category_id": cat_id,
                "sku": "ARG-001",
                "barcode": "8901234567890",
                "cost_price": 400.0,
                "retail_price": 800.0,
                "tax_rate": 18.0,
                "stock_quantity": 10,
                "low_stock_threshold": 3,
            },
        )
        assert res.status_code == 201
        product_id = res.json()["id"]
        assert res.json()["stock_quantity"] == 10
        assert res.json()["is_low_stock"] is False

        # 3. Record Stock Movement (Restock +5)
        res = await client.post(
            f"/api/v1/businesses/{business.id}/inventory/movements",
            headers=_header(owner_token),
            json={
                "product_id": product_id,
                "movement_type": "IN",
                "quantity": 5,
                "unit_cost": 400.0,
                "notes": "Weekly supplier restock",
            },
        )
        assert res.status_code == 201

        # Check updated stock
        res = await client.get(
            f"/api/v1/businesses/{business.id}/inventory/products/{product_id}",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert res.json()["stock_quantity"] == 15

        # 4. Record Stock Movement (Write-off OUT -13 -> remaining 2)
        res = await client.post(
            f"/api/v1/businesses/{business.id}/inventory/movements",
            headers=_header(owner_token),
            json={
                "product_id": product_id,
                "movement_type": "OUT",
                "quantity": 13,
                "notes": "Internal salon usage",
            },
        )
        assert res.status_code == 201

        # Check low stock flag triggered
        res = await client.get(
            f"/api/v1/businesses/{business.id}/inventory/products/{product_id}",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert res.json()["stock_quantity"] == 2
        assert res.json()["is_low_stock"] is True


@pytest.mark.asyncio
class TestPhase3Memberships:
    """2. Membership Plans & Customer Subscriptions Tests"""

    async def test_memberships_flow(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, _, _, owner_token = business_with_owner
        customer, cust_token = customer_user

        # 1. Create Membership Plan
        res = await client.post(
            f"/api/v1/businesses/{business.id}/memberships/plans",
            headers=_header(owner_token),
            json={
                "name": "Zenglow VIP Club",
                "description": "15% off all services + 2 free hair treatments",
                "price": 2999.0,
                "duration_months": 12,
                "discount_percentage": 15.0,
                "free_services_count": 2,
            },
        )
        assert res.status_code == 201
        plan_id = res.json()["id"]

        # 2. Enroll Customer
        res = await client.post(
            f"/api/v1/businesses/{business.id}/memberships/enroll",
            headers=_header(owner_token),
            json={
                "customer_id": str(customer.id),
                "plan_id": plan_id,
                "notes": "Paid annual subscription",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "ACTIVE"
        assert data["free_services_remaining"] == 2

        # 3. List Customer Memberships
        res = await client.get(
            f"/api/v1/businesses/{business.id}/memberships/customers?customer_id={customer.id}",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert len(res.json()) >= 1


@pytest.mark.asyncio
class TestPhase3Packages:
    """3. Bundled Packages & Redemptions Tests"""

    async def test_packages_flow(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, branch, _, owner_token = business_with_owner
        service, staff = await _setup_phase3_business(db, business, branch, roles)
        customer, _ = customer_user

        # 1. Create Package Template
        res = await client.post(
            f"/api/v1/businesses/{business.id}/packages/templates",
            headers=_header(owner_token),
            json={
                "name": "Luxury Spa 3-Session Bundle",
                "description": "3 sessions of Spa Deluxe",
                "price": 3500.0,
                "validity_days": 90,
                "items": [{"service_id": str(service.id), "quantity": 3}],
            },
        )
        assert res.status_code == 201
        template_id = res.json()["id"]

        # 2. Sell Package to Customer
        res = await client.post(
            f"/api/v1/businesses/{business.id}/packages/sell",
            headers=_header(owner_token),
            json={
                "customer_id": str(customer.id),
                "package_template_id": template_id,
            },
        )
        assert res.status_code == 201
        cust_pkg_id = res.json()["id"]
        assert res.json()["status"] == "ACTIVE"
        assert res.json()["items"][0]["remaining_quantity"] == 3

        # 3. Redeem 1 Session
        res = await client.post(
            f"/api/v1/businesses/{business.id}/packages/customers/{cust_pkg_id}/redeem",
            headers=_header(owner_token),
            json={"service_id": str(service.id)},
        )
        assert res.status_code == 200
        assert res.json()["used_quantity"] == 1
        assert res.json()["remaining_quantity"] == 2


@pytest.mark.asyncio
class TestPhase3GiftCards:
    """4. Gift Card Issuance & Redemptions Tests"""

    async def test_gift_card_flow(
        self, client: AsyncClient, db: AsyncSession, business_with_owner
    ):
        business, _, _, owner_token = business_with_owner

        # 1. Issue Gift Card
        res = await client.post(
            f"/api/v1/businesses/{business.id}/gift-cards",
            headers=_header(owner_token),
            json={
                "amount": 2000.0,
                "recipient_name": "Anita Roy",
                "recipient_email": "anita@example.com",
                "message": "Happy Birthday!",
                "expiry_days": 365,
            },
        )
        assert res.status_code == 201
        gc_data = res.json()
        code = gc_data["code"]
        assert gc_data["initial_balance"] == 2000.0
        assert gc_data["current_balance"] == 2000.0

        # 2. Check Balance
        res = await client.get(
            f"/api/v1/businesses/{business.id}/gift-cards/check/{code}",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert res.json()["valid"] is True
        assert res.json()["current_balance"] == 2000.0

        # 3. Redeem Balance (₹500)
        res = await client.post(
            f"/api/v1/businesses/{business.id}/gift-cards/redeem",
            headers=_header(owner_token),
            json={"code": code, "amount": 500.0},
        )
        assert res.status_code == 200
        assert res.json()["current_balance"] == 1500.0


@pytest.mark.asyncio
class TestPhase3POS:
    """5. Point-of-Sale Checkout & Order Management Tests"""

    async def test_pos_checkout_flow(
        self, client: AsyncClient, db: AsyncSession, business_with_owner, customer_user, roles
    ):
        business, branch, _, owner_token = business_with_owner
        service, staff = await _setup_phase3_business(db, business, branch, roles)
        customer, _ = customer_user

        # Create a product with stock = 20
        res = await client.post(
            f"/api/v1/businesses/{business.id}/inventory/products",
            headers=_header(owner_token),
            json={
                "name": "Styling Wax Pro",
                "cost_price": 200.0,
                "retail_price": 500.0,
                "tax_rate": 18.0,
                "stock_quantity": 20,
            },
        )
        product_id = res.json()["id"]

        # Issue Gift Card with ₹500
        gc_res = await client.post(
            f"/api/v1/businesses/{business.id}/gift-cards",
            headers=_header(owner_token),
            json={"amount": 500.0, "recipient_name": "Test User"},
        )
        gc_code = gc_res.json()["code"]

        # Cart: Service ₹1500 (18% tax = 270) + Product ₹500 (18% tax = 90) = Total ₹2360
        # Split Payment: ₹500 Gift Card + ₹1860 Cash
        res = await client.post(
            f"/api/v1/businesses/{business.id}/pos/checkout",
            headers=_header(owner_token),
            json={
                "branch_id": str(branch.id),
                "customer_id": str(customer.id),
                "staff_id": str(staff.id),
                "items": [
                    {
                        "item_type": "SERVICE",
                        "item_id": str(service.id),
                        "name": "Phase 3 Spa Deluxe",
                        "quantity": 1,
                        "unit_price": 1500.0,
                        "tax_rate": 18.0,
                        "discount_amount": 0.0,
                    },
                    {
                        "item_type": "PRODUCT",
                        "item_id": str(product_id),
                        "name": "Styling Wax Pro",
                        "quantity": 1,
                        "unit_price": 500.0,
                        "tax_rate": 18.0,
                        "discount_amount": 0.0,
                    },
                ],
                "payments": [
                    {
                        "payment_method": "GIFT_CARD",
                        "amount": 500.0,
                        "reference_code": gc_code,
                    },
                    {
                        "payment_method": "CASH",
                        "amount": 1860.0,
                    },
                ],
                "discount_amount": 0.0,
                "tip_amount": 0.0,
                "notes": "Front-desk POS checkout",
            },
        )
        assert res.status_code == 201
        order_data = res.json()
        assert order_data["status"] == "COMPLETED"
        assert order_data["total_amount"] == 2360.0
        assert len(order_data["items"]) == 2
        assert len(order_data["payments"]) == 2

        # Verify product stock decremented from 20 -> 19
        prod_chk = await client.get(
            f"/api/v1/businesses/{business.id}/inventory/products/{product_id}",
            headers=_header(owner_token),
        )
        assert prod_chk.json()["stock_quantity"] == 19


@pytest.mark.asyncio
class TestPhase3Reports:
    """6. Reports & Business Operations Analytics Tests"""

    async def test_reports_endpoints(
        self, client: AsyncClient, db: AsyncSession, business_with_owner
    ):
        business, _, _, owner_token = business_with_owner

        # 1. Revenue Report
        res = await client.get(
            f"/api/v1/businesses/{business.id}/reports/revenue",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert "total_revenue" in res.json()

        # 2. Staff Performance Report
        res = await client.get(
            f"/api/v1/businesses/{business.id}/reports/staff",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert "metrics" in res.json()

        # 3. Inventory Report
        res = await client.get(
            f"/api/v1/businesses/{business.id}/reports/inventory",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert "total_valuation_retail" in res.json()

        # 4. Operations Summary
        res = await client.get(
            f"/api/v1/businesses/{business.id}/reports/operations",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert "total_bookings" in res.json()
        assert "active_memberships" in res.json()
