"""
Business and Branch CRUD tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBusinessCRUD:
    async def test_create_business(self, client: AsyncClient, customer_user):
        _, token = customer_user
        res = await client.post(
            "/api/v1/businesses",
            json={
                "name": "My Salon",
                "category": "SALON",
                "instagram_url": "https://instagram.com/mysalon",
                "facebook_url": "https://facebook.com/mysalon",
                "tiktok_url": "https://tiktok.com/@mysalon",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "My Salon"
        assert data["slug"] == "my-salon"
        assert data["status"] == "ACTIVE"
        assert len(data["branches"]) == 1  # primary branch auto-created
        assert data["instagram_url"] == "https://instagram.com/mysalon"
        assert data["facebook_url"] == "https://facebook.com/mysalon"
        assert data["tiktok_url"] == "https://tiktok.com/@mysalon"

    async def test_create_business_requires_auth(self, client: AsyncClient):
        res = await client.post("/api/v1/businesses", json={"name": "Salon", "category": "SALON"})
        assert res.status_code == 401

    async def test_list_my_businesses(self, client: AsyncClient, business_with_owner):
        business, _, owner, token = business_with_owner
        res = await client.get(
            "/api/v1/businesses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        ids = [b["id"] for b in res.json()["items"]]
        assert str(business.id) in ids

    async def test_get_business_by_id(self, client: AsyncClient, business_with_owner):
        business, _, owner, token = business_with_owner
        res = await client.get(
            f"/api/v1/businesses/{business.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["id"] == str(business.id)

    async def test_update_business(self, client: AsyncClient, business_with_owner):
        business, _, owner, token = business_with_owner
        res = await client.patch(
            f"/api/v1/businesses/{business.id}",
            json={
                "description": "Updated description",
                "instagram_url": "https://instagram.com/glowstudio",
                "facebook_url": "https://facebook.com/glowstudio",
                "tiktok_url": "https://tiktok.com/@glowstudio",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["description"] == "Updated description"
        assert data["instagram_url"] == "https://instagram.com/glowstudio"
        assert data["facebook_url"] == "https://facebook.com/glowstudio"
        assert data["tiktok_url"] == "https://tiktok.com/@glowstudio"

    async def test_social_urls_reject_invalid_urls(
        self, client: AsyncClient, business_with_owner
    ):
        business, _, owner, token = business_with_owner
        res = await client.patch(
            f"/api/v1/businesses/{business.id}",
            json={"instagram_url": "javascript:alert(1)"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422

    async def test_search_businesses(self, client: AsyncClient, business_with_owner):
        res = await client.get("/api/v1/businesses/search?q=Test")
        assert res.status_code == 200
        assert "items" in res.json()

    async def test_slug_collision_resolved(self, client: AsyncClient, customer_user):
        _, token = customer_user
        headers = {"Authorization": f"Bearer {token}"}
        await client.post("/api/v1/businesses", json={"name": "Unique Salon", "category": "SALON"}, headers=headers)
        res2 = await client.post("/api/v1/businesses", json={"name": "Unique Salon", "category": "SALON"}, headers=headers)
        assert res2.status_code == 201
        # Second slug should be different
        assert res2.json()["slug"] != "unique-salon"


@pytest.mark.asyncio
class TestBranchCRUD:
    async def test_create_branch(self, client: AsyncClient, business_with_owner):
        business, _, owner, token = business_with_owner
        res = await client.post(
            f"/api/v1/businesses/{business.id}/branches",
            json={"name": "Second Branch", "city": "Delhi"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        assert res.json()["name"] == "Second Branch"

    async def test_list_branches(self, client: AsyncClient, business_with_owner):
        business, _, owner, token = business_with_owner
        res = await client.get(
            f"/api/v1/businesses/{business.id}/branches",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert len(res.json()) >= 1
