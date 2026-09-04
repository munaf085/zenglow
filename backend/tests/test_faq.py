"""
FAQ CRUD tests.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestFAQCRUD:

    async def test_create_faq(
        self,
        client: AsyncClient,
        business_with_owner,
    ):
        business, _, _, token = business_with_owner

        res = await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "What are your opening hours?",
                "answer": "We are open from 9 AM to 6 PM.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 201

        data = res.json()

        assert data["business_id"] == str(business.id)
        assert data["question"] == "What are your opening hours?"
        assert data["answer"] == "We are open from 9 AM to 6 PM."

    async def test_create_faq_requires_auth(
        self,
        client: AsyncClient,
        business_with_owner,
    ):
        business, _, _, _ = business_with_owner

        res = await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "Do you offer home service?",
                "answer": "Yes, we do.",
            },
        )

        assert res.status_code == 401

    async def test_list_faqs(
        self,
        client: AsyncClient,
        business_with_owner,
    ):
        business, _, _, token = business_with_owner

        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "What services do you offer?",
                "answer": "Hair, skin, and beauty services.",
            },
            headers=headers,
        )

        await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "Do I need an appointment?",
                "answer": "Appointments are recommended.",
            },
            headers=headers,
        )

        res = await client.get(
            f"/api/v1/businesses/{business.id}/faqs",
            headers=headers,
        )

        assert res.status_code == 200

        data = res.json()

        assert len(data) == 2
        assert data[0]["question"] == "What services do you offer?"
        assert data[1]["question"] == "Do I need an appointment?"

    async def test_get_faq(
        self,
        client: AsyncClient,
        business_with_owner,
    ):
        business, _, _, token = business_with_owner

        headers = {"Authorization": f"Bearer {token}"}

        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "Do you accept walk-ins?",
                "answer": "Yes, depending on availability.",
            },
            headers=headers,
        )

        assert create_res.status_code == 201

        faq_id = create_res.json()["id"]

        res = await client.get(
            f"/api/v1/businesses/{business.id}/faqs/{faq_id}",
            headers=headers,
        )

        assert res.status_code == 200

        data = res.json()

        assert data["id"] == faq_id
        assert data["question"] == "Do you accept walk-ins?"
        assert data["answer"] == "Yes, depending on availability."

    async def test_list_faqs_requires_auth(
        self,
        client: AsyncClient,
        business_with_owner,
    ):
        business, _, _, _ = business_with_owner

        res = await client.get(
            f"/api/v1/businesses/{business.id}/faqs",
        )

        assert res.status_code == 401

    async def test_get_faq_requires_auth(
        self,
        client: AsyncClient,
        business_with_owner,
    ):
        business, _, _, token = business_with_owner

        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "Are children allowed?",
                "answer": "Yes.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert create_res.status_code == 201

        faq_id = create_res.json()["id"]

        res = await client.get(
            f"/api/v1/businesses/{business.id}/faqs/{faq_id}",
        )

        assert res.status_code == 401

    async def test_faq_business_isolation(
        self,
        client: AsyncClient,
        business_with_owner,
        roles,
        db,
    ):
        business, _, _, owner_token = business_with_owner

        # Create FAQ for the first business.
        create_res = await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "Private question",
                "answer": "Private answer",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert create_res.status_code == 201

        faq_id = create_res.json()["id"]

        # Create a second business and owner.
        from app.models.business import (
            Business,
            BusinessCategory,
            BusinessStatus,
        )
        from app.models.user import UserRole
        from app.core.security import create_access_token, hash_password
        from app.models.user import RoleEnum
        import uuid

        second_owner_email = (
            f"second_owner_{uuid.uuid4().hex[:8]}@test.com"
        )

        from app.models.user import User

        second_owner = User(
            email=second_owner_email,
            first_name="Second",
            last_name="Owner",
            hashed_password=hash_password("Test@1234"),
            is_active=True,
            is_verified=True,
        )

        db.add(second_owner)
        await db.flush()

        owner_role = roles[RoleEnum.BUSINESS_OWNER.value]

        second_business = Business(
            owner_id=second_owner.id,
            name="Second Salon",
            slug=f"second-salon-{uuid.uuid4().hex[:6]}",
            category=BusinessCategory.SALON,
            status=BusinessStatus.ACTIVE,
        )

        db.add(second_business)
        await db.flush()

        db.add(
            UserRole(
                user_id=second_owner.id,
                role_id=owner_role.id,
                business_id=second_business.id,
            )
        )

        await db.flush()

        second_token = create_access_token(
            str(second_owner.id),
            extra_claims={
                "roles": [RoleEnum.BUSINESS_OWNER.value],
            },
        )

        # Second owner must not access first business FAQ.
        res = await client.get(
            f"/api/v1/businesses/{business.id}/faqs/{faq_id}",
            headers={"Authorization": f"Bearer {second_token}"},
        )

        assert res.status_code in (403, 404)

        res = await client.get(
            f"/api/v1/businesses/{business.id}/faqs",
            headers={"Authorization": f"Bearer {second_token}"},
        )

        assert res.status_code in (403, 404)

    async def test_public_faqs(
        self,
        client: AsyncClient,
        business_with_owner,
    ):
        business, _, _, token = business_with_owner

        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            f"/api/v1/businesses/{business.id}/faqs",
            json={
                "question": "What payment methods do you accept?",
                "answer": "We accept cash and cards.",
            },
            headers=headers,
        )

        res = await client.get(
            f"/api/v1/businesses/public/{business.slug}/faqs",
        )

        assert res.status_code == 200

        data = res.json()

        assert len(data) == 1
        assert data[0]["question"] == (
            "What payment methods do you accept?"
        )
        assert data[0]["answer"] == "We accept cash and cards."

    async def test_public_faqs_requires_active_business(
        self,
        client: AsyncClient,
        business_with_owner,
        db,
    ):
        business, _, _, _ = business_with_owner

        from app.models.business import BusinessStatus

        business.status = BusinessStatus.DEACTIVATED
        db.add(business)
        await db.flush()

        res = await client.get(
            f"/api/v1/businesses/public/{business.slug}/faqs",
        )

        assert res.status_code == 404