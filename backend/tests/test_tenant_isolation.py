"""
Tenant isolation tests — critical security requirement.
Business A must never be able to read or modify Business B's data.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import _make_user
from app.models.user import RoleEnum


@pytest.mark.asyncio
class TestTenantIsolation:
    """
    All tests in this class verify that cross-tenant access is rejected.
    """

    async def test_owner_cannot_read_other_business(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles: dict
    ):
        """Owner of business A cannot read business B."""
        business_a, _, owner_a, token_a = business_with_owner

        # Create a second owner + business B
        _, token_b = await _make_user(db, roles, "owner_b@test.com", RoleEnum.CUSTOMER.value)
        res = await client.post(
            "/api/v1/businesses",
            json={"name": "Business B", "category": "SPA"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        business_b_id = res.json()["id"]

        # Owner A tries to read Business B — should get 404 (tenant isolation hides existence)
        res = await client.get(
            f"/api/v1/businesses/{business_b_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 404

    async def test_owner_cannot_update_other_business(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles: dict
    ):
        """Owner of business A cannot update business B."""
        _, _, _, token_a = business_with_owner

        _, token_b = await _make_user(db, roles, "owner_b2@test.com", RoleEnum.CUSTOMER.value)
        res = await client.post(
            "/api/v1/businesses",
            json={"name": "Business B2", "category": "SPA"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        business_b_id = res.json()["id"]

        res = await client.patch(
            f"/api/v1/businesses/{business_b_id}",
            json={"description": "Hacked by A"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 404

    async def test_owner_cannot_manage_other_business_staff(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles: dict
    ):
        """Owner A cannot add staff to Business B."""
        _, _, _, token_a = business_with_owner

        _, token_b = await _make_user(db, roles, "owner_b3@test.com", RoleEnum.CUSTOMER.value)
        res = await client.post(
            "/api/v1/businesses",
            json={"name": "Business B3", "category": "SALON"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        business_b_id = res.json()["id"]

        res = await client.post(
            f"/api/v1/businesses/{business_b_id}/staff",
            json={"first_name": "Hacker", "last_name": "Staff"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 404

    async def test_owner_cannot_manage_other_business_services(
        self, client: AsyncClient, business_with_owner, db: AsyncSession, roles: dict
    ):
        """Owner A cannot create services in Business B."""
        _, _, _, token_a = business_with_owner

        _, token_b = await _make_user(db, roles, "owner_b4@test.com", RoleEnum.CUSTOMER.value)
        res = await client.post(
            "/api/v1/businesses",
            json={"name": "Business B4", "category": "SALON"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        business_b_id = res.json()["id"]

        res = await client.post(
            f"/api/v1/businesses/{business_b_id}/services",
            json={"name": "Stolen Service", "price": 100, "duration_minutes": 30},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 404

    async def test_unauthenticated_cannot_access_protected_routes(self, client: AsyncClient):
        """All protected routes require authentication."""
        routes = [
            ("GET", "/api/v1/businesses"),
            ("POST", "/api/v1/businesses"),
            ("GET", "/api/v1/auth/me"),
            ("GET", "/api/v1/bookings/me"),
        ]
        for method, path in routes:
            res = await client.request(method, path)
            assert res.status_code == 401, f"{method} {path} should be 401, got {res.status_code}"

    async def test_admin_can_access_all_businesses(
        self, client: AsyncClient, business_with_owner, admin_user
    ):
        """Platform admin bypasses tenant isolation."""
        business, _, _, _ = business_with_owner
        _, admin_token = admin_user

        res = await client.get(
            "/api/v1/admin/businesses",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res.status_code == 200

    async def test_non_admin_cannot_access_admin_routes(
        self, client: AsyncClient, customer_user
    ):
        """Regular users cannot access admin routes."""
        _, token = customer_user
        res = await client.get(
            "/api/v1/admin/businesses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
