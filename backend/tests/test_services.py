"""
Service and staff management tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestServiceCRUD:
    async def test_create_service(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        res = await client.post(
            f"/api/v1/businesses/{business.id}/services",
            json={"name": "Haircut", "price": 500, "duration_minutes": 45, "tax_rate": 18},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Haircut"
        assert data["price"] == 500.0
        assert data["duration_minutes"] == 45

    async def test_list_services_public(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        await client.post(
            f"/api/v1/businesses/{business.id}/services",
            json={"name": "Massage", "price": 1000, "duration_minutes": 60},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Public listing (no auth)
        res = await client.get(f"/api/v1/businesses/{business.id}/services")
        assert res.status_code == 200
        names = [s["name"] for s in res.json()]
        assert "Massage" in names

    async def test_update_service(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/services",
            json={"name": "Old Name", "price": 200, "duration_minutes": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        service_id = create_res.json()["id"]

        res = await client.patch(
            f"/api/v1/businesses/{business.id}/services/{service_id}",
            json={"name": "New Name", "price": 250},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["name"] == "New Name"
        assert res.json()["price"] == 250.0

    async def test_delete_service(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/services",
            json={"name": "Delete Me", "price": 100, "duration_minutes": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        service_id = create_res.json()["id"]

        res = await client.delete(
            f"/api/v1/businesses/{business.id}/services/{service_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

        # Verify it's gone from public listing
        list_res = await client.get(f"/api/v1/businesses/{business.id}/services")
        ids = [s["id"] for s in list_res.json()]
        assert service_id not in ids

    async def test_service_belongs_to_business(self, client: AsyncClient, business_with_owner, customer_user):
        business, _, _, owner_token = business_with_owner
        _, cust_token = customer_user

        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/services",
            json={"name": "Private Svc", "price": 300, "duration_minutes": 30},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        service_id = create_res.json()["id"]

        # Customer tries to delete owner's service
        res = await client.delete(
            f"/api/v1/businesses/{business.id}/services/{service_id}",
            headers={"Authorization": f"Bearer {cust_token}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
class TestStaffCRUD:
    async def test_create_staff(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        res = await client.post(
            f"/api/v1/businesses/{business.id}/staff",
            json={"first_name": "Jane", "last_name": "Doe", "title": "Stylist"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["first_name"] == "Jane"
        assert data["status"] == "ACTIVE"

    async def test_list_staff(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        await client.post(
            f"/api/v1/businesses/{business.id}/staff",
            json={"first_name": "John", "last_name": "Smith"},
            headers={"Authorization": f"Bearer {token}"},
        )
        res = await client.get(
            f"/api/v1/businesses/{business.id}/staff",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert len(res.json()) >= 1

    async def test_update_staff(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/staff",
            json={"first_name": "Old", "last_name": "Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        staff_id = create_res.json()["id"]

        res = await client.patch(
            f"/api/v1/businesses/{business.id}/staff/{staff_id}",
            json={"first_name": "New", "title": "Senior Stylist"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["first_name"] == "New"

    async def test_working_hours_crud(self, client: AsyncClient, business_with_owner):
        business, _, _, token = business_with_owner
        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/staff",
            json={"first_name": "Hours", "last_name": "Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        staff_id = create_res.json()["id"]

        hours = [
            {"day_of_week": i, "is_open": i < 5, "open_time": "09:00" if i < 5 else None, "close_time": "18:00" if i < 5 else None}
            for i in range(7)
        ]
        res = await client.put(
            f"/api/v1/businesses/{business.id}/staff/{staff_id}/working-hours",
            json={"hours": hours},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert len(res.json()) == 7
