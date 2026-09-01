"""
Authentication tests: register, login, refresh, logout, password change.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        res = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "Secure@123",
            "first_name": "New",
            "last_name": "User",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "newuser@example.com"
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"email": "dup@example.com", "password": "Secure@123", "first_name": "A", "last_name": "B"}
        await client.post("/api/v1/auth/register", json=payload)
        res = await client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 409
        assert res.json()["error"]["code"] == "CONFLICT"

    async def test_register_weak_password(self, client: AsyncClient):
        res = await client.post("/api/v1/auth/register", json={
            "email": "weak@example.com",
            "password": "password",  # no uppercase, no digit
            "first_name": "A",
            "last_name": "B",
        })
        assert res.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        res = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Secure@123",
            "first_name": "A",
            "last_name": "B",
        })
        assert res.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "login@example.com",
            "password": "Login@1234",
            "first_name": "Login",
            "last_name": "User",
        })
        res = await client.post("/api/v1/auth/login", json={
            "email": "login@example.com",
            "password": "Login@1234",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "wrongpw@example.com",
            "password": "Correct@1",
            "first_name": "A", "last_name": "B",
        })
        res = await client.post("/api/v1/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "Wrong@999",
        })
        assert res.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        res = await client.post("/api/v1/auth/login", json={
            "email": "ghost@example.com",
            "password": "Ghost@1234",
        })
        assert res.status_code == 401


@pytest.mark.asyncio
class TestTokens:
    async def test_refresh_token(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "refresh@example.com",
            "password": "Refresh@1",
            "first_name": "A", "last_name": "B",
        })
        login_res = await client.post("/api/v1/auth/login", json={
            "email": "refresh@example.com", "password": "Refresh@1",
        })
        refresh_token = login_res.json()["refresh_token"]

        res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert res.status_code == 200
        assert "access_token" in res.json()

    async def test_me_requires_auth(self, client: AsyncClient):
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 401

    async def test_me_with_valid_token(self, client: AsyncClient, customer_user):
        user, token = customer_user
        res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["id"] == str(user.id)
