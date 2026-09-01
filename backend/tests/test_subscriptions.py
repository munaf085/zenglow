"""
Subscription Checkout & Plan Upgrade Tests.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.subscription import BillingCycle, PlanTier, Subscription, SubscriptionPlan, SubscriptionStatus


def _header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestSubscriptionFlow:
    async def test_list_plans(self, client: AsyncClient, business_with_owner):
        business, _, _, owner_token = business_with_owner

        res = await client.get("/api/v1/subscriptions/plans")
        assert res.status_code == 200
        plans = res.json()
        assert len(plans) >= 3
        tiers = [p["tier"] for p in plans]
        assert "STARTER" in tiers
        assert "PROFESSIONAL" in tiers
        assert "ENTERPRISE" in tiers

    async def test_create_order_and_verify_upgrade(
        self, client: AsyncClient, db: AsyncSession, business_with_owner
    ):
        business, _, _, owner_token = business_with_owner

        # 1. Get plans
        res = await client.get("/api/v1/subscriptions/plans")
        assert res.status_code == 200
        pro_plan = next(p for p in res.json() if p["tier"] == "PROFESSIONAL")

        # 2. Create Order
        res = await client.post(
            "/api/v1/subscriptions/create-order",
            headers=_header(owner_token),
            json={
                "business_id": str(business.id),
                "plan_id": pro_plan["id"],
                "billing_cycle": "MONTHLY",
            },
        )
        assert res.status_code == 201
        order_data = res.json()
        assert "provider_order_id" in order_data
        assert order_data["amount"] == 2499.0
        assert order_data["currency"] == "INR"

        order_id = order_data["provider_order_id"]
        payment_id = "mock_pay_12345"
        signature = "mock_sig_123"

        res = await client.post(
            "/api/v1/subscriptions/verify",
            headers=_header(owner_token),
            json={
                "business_id": str(business.id),
                "plan_id": pro_plan["id"],
                "billing_cycle": "MONTHLY",
                "provider_payment_id": payment_id,
                "provider_order_id": order_id,
                "provider_signature": signature,
            },
        )
        assert res.status_code == 200
        sub_data = res.json()
        assert sub_data["status"] == "ACTIVE"
        assert sub_data["billing_cycle"] == "MONTHLY"
        assert sub_data["plan"]["tier"] == "PROFESSIONAL"

        # 4. Verify Business Model in DB was upgraded
        biz_db = (
            await db.execute(select(Business).where(Business.id == business.id))
        ).scalar_one()
        assert str(biz_db.subscription_plan_id) == str(pro_plan["id"])

        # 5. Check Current Subscription endpoint
        res = await client.get(
            f"/api/v1/subscriptions/businesses/{business.id}/current",
            headers=_header(owner_token),
        )
        assert res.status_code == 200
        assert res.json()["plan"]["tier"] == "PROFESSIONAL"

    async def test_invalid_signature_rejected(
        self, client: AsyncClient, business_with_owner
    ):
        business, _, _, owner_token = business_with_owner

        res = await client.get("/api/v1/subscriptions/plans")
        starter_plan = next(p for p in res.json() if p["tier"] == "STARTER")

        # Attempt verification with non-mock / invalid signature
        res = await client.post(
            "/api/v1/subscriptions/verify",
            headers=_header(owner_token),
            json={
                "business_id": str(business.id),
                "plan_id": starter_plan["id"],
                "billing_cycle": "MONTHLY",
                "provider_payment_id": "invalid_pay_999",
                "provider_order_id": "order_fake_999",
                "provider_signature": "invalid_forged_sig",
            },
        )
        assert res.status_code == 402
