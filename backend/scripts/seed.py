"""
Development seed data script.
Creates realistic data for local development and demos.

Run: python scripts/seed.py

Demo credentials:
  Platform Admin: admin@zenglow.com     / Admin@1234
  Business Owner: owner@glowstudio.com  / Owner@1234
  Staff:          staff@glowstudio.com  / Staff@1234
  Customer:       customer@example.com  / Customer@1234
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure the backend root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.models import *  # noqa — registers all models
from app.db.base import Base
from app.models.user import Role, RoleEnum, User, UserRole, Permission, RolePermission
from app.models.business import Branch, Business, BusinessCategory, BusinessStatus
from app.models.service import Service, ServiceCategory
from app.models.staff import Staff, StaffLeave, StaffService as StaffServiceModel, WorkingHours
from app.models.customer import Customer
from app.models.appointment import Appointment, AppointmentItem, AppointmentStatus
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.subscription import BillingCycle, SubscriptionPlan, SubscriptionStatus, PlanTier, Subscription


async def seed():
    print("🌱 Seeding development database...")

    async with AsyncSessionLocal() as db:
        # ── Roles & Permissions ──────────────────────────────────────────────
        print("  Creating roles and permissions...")
        roles = {}
        for role_enum in RoleEnum:
            existing = (await db.execute(select(Role).where(Role.name == role_enum.value))).scalar_one_or_none()
            if not existing:
                role = Role(name=role_enum.value, description=f"{role_enum.value} role", is_system=True)
                db.add(role)
                await db.flush()
                roles[role_enum.value] = role
            else:
                roles[role_enum.value] = existing

        # ── Permissions ──────────────────────────────────────────────────────
        from app.core.permissions import ROLE_PERMISSIONS
        perm_map = {}
        for role_name, perms in ROLE_PERMISSIONS.items():
            for perm_name in perms:
                if perm_name not in perm_map:
                    existing = (await db.execute(select(Permission).where(Permission.name == perm_name))).scalar_one_or_none()
                    if not existing:
                        perm = Permission(name=perm_name, description=perm_name)
                        db.add(perm)
                        await db.flush()
                        perm_map[perm_name] = perm
                    else:
                        perm_map[perm_name] = existing
                # Link role -> permission
                role = roles.get(role_name)
                if role:
                    existing_rp = (await db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == role.id,
                            RolePermission.permission_id == perm_map[perm_name].id
                        )
                    )).scalar_one_or_none()
                    if not existing_rp:
                        rp = RolePermission(role_id=role.id, permission_id=perm_map[perm_name].id)
                        db.add(rp)
        await db.flush()

        # ── Subscription Plans ────────────────────────────────────────────────
        print("  Creating subscription plans...")
        plan_data = [
            {"tier": PlanTier.FREE, "name": "Free", "monthly_price": 0, "yearly_price": 0,
             "max_branches": 1, "max_staff": 2, "max_services": 10, "max_bookings_per_month": 50},
            {"tier": PlanTier.STARTER, "name": "Starter", "monthly_price": 999, "yearly_price": 9990,
             "max_branches": 1, "max_staff": 5, "max_services": 20, "max_bookings_per_month": 200},
            {"tier": PlanTier.PROFESSIONAL, "name": "Professional", "monthly_price": 2499, "yearly_price": 24990,
             "max_branches": 3, "max_staff": 15, "max_services": 50, "max_bookings_per_month": 1000},
            {"tier": PlanTier.ENTERPRISE, "name": "Enterprise", "monthly_price": 5999, "yearly_price": 59990,
             "max_branches": 999, "max_staff": 999, "max_services": 999, "max_bookings_per_month": 9999},
        ]
        plans = {}
        for pd in plan_data:
            existing = (await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.tier == pd["tier"])
            )).scalar_one_or_none()
            if not existing:
                plan = SubscriptionPlan(currency="INR", **pd)
                db.add(plan)
                await db.flush()
                plans[pd["tier"]] = plan
            else:
                plans[pd["tier"]] = existing

        # ── Users ─────────────────────────────────────────────────────────────
        print("  Creating users...")

        async def create_user(email, first, last, password, role_name, is_superuser=False):
            existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if existing:
                return existing
            user = User(
                email=email,
                first_name=first,
                last_name=last,
                hashed_password=hash_password(password),
                is_active=True,
                is_verified=True,
                is_superuser=is_superuser,
            )
            db.add(user)
            await db.flush()
            # Assign role (platform-level)
            role = roles.get(role_name)
            if role:
                ur = UserRole(user_id=user.id, role_id=role.id, business_id=None)
                db.add(ur)
                await db.flush()
            return user

        admin_user = await create_user(
            "admin@zenglow.com", "Platform", "Admin", "Admin@1234",
            RoleEnum.PLATFORM_ADMIN.value, is_superuser=True
        )
        owner_user = await create_user(
            "owner@glowstudio.com", "Sarah", "Johnson", "Owner@1234",
            RoleEnum.CUSTOMER.value  # will be upgraded to BUSINESS_OWNER when business created
        )
        owner2_user = await create_user(
            "owner@urbancuts.com", "Mike", "Chen", "Owner@1234",
            RoleEnum.CUSTOMER.value
        )
        owner3_user = await create_user(
            "owner@serenityspa.com", "Priya", "Sharma", "Owner@1234",
            RoleEnum.CUSTOMER.value
        )
        staff_user = await create_user(
            "staff@glowstudio.com", "Alex", "Thompson", "Staff@1234",
            RoleEnum.CUSTOMER.value
        )
        customer_user = await create_user(
            "customer@example.com", "Emma", "Wilson", "Customer@1234",
            RoleEnum.CUSTOMER.value
        )
        customer2_user = await create_user(
            "customer2@example.com", "Raj", "Patel", "Customer@1234",
            RoleEnum.CUSTOMER.value
        )

        # ── Customer Profiles ─────────────────────────────────────────────────
        async def ensure_customer(user):
            existing = (await db.execute(select(Customer).where(Customer.user_id == user.id))).scalar_one_or_none()
            if not existing:
                c = Customer(user_id=user.id)
                db.add(c)
                await db.flush()
                return c
            return existing

        await ensure_customer(owner_user)
        await ensure_customer(owner2_user)
        await ensure_customer(owner3_user)
        await ensure_customer(staff_user)
        customer = await ensure_customer(customer_user)
        customer2 = await ensure_customer(customer2_user)

        # ── Business 1: Glow Studio ───────────────────────────────────────────
        print("  Creating Business 1: Glow Studio...")
        existing_biz = (await db.execute(select(Business).where(Business.slug == "glow-studio"))).scalar_one_or_none()
        if not existing_biz:
            glow = Business(
                owner_id=owner_user.id,
                name="Glow Studio",
                slug="glow-studio",
                category=BusinessCategory.SALON,
                description="Premium hair and beauty salon in the heart of the city.",
                email="hello@glowstudio.com",
                phone="+91 98765 43210",
                status=BusinessStatus.ACTIVE,
                is_verified=True,
                booking_advance_days=60,
                cancellation_hours=24,
                subscription_plan_id=plans[PlanTier.PROFESSIONAL].id,
            )
            db.add(glow)
            await db.flush()

            # Assign BUSINESS_OWNER role
            bo_role = roles[RoleEnum.BUSINESS_OWNER.value]
            ur = UserRole(user_id=owner_user.id, role_id=bo_role.id, business_id=glow.id)
            db.add(ur)

            # Branch
            glow_branch = Branch(
                business_id=glow.id, name="Main Branch", is_primary=True, is_active=True,
                address_line1="42 Fashion Street", city="Mumbai", state="Maharashtra",
                country="India", postal_code="400001", phone="+91 98765 43210",
            )
            db.add(glow_branch)
            await db.flush()

            # Working hours Mon-Sat
            for day in range(7):
                wh = WorkingHours(
                    entity_type="branch", entity_id=glow_branch.id, business_id=glow.id,
                    day_of_week=day, is_open=day < 6,
                    open_time="09:00" if day < 6 else None,
                    close_time="20:00" if day < 6 else None,
                )
                db.add(wh)

            # Service categories
            cat_hair = ServiceCategory(business_id=glow.id, name="Hair", color="#E91E8C", sort_order=1)
            cat_nails = ServiceCategory(business_id=glow.id, name="Nails", color="#9C27B0", sort_order=2)
            cat_skin = ServiceCategory(business_id=glow.id, name="Skin", color="#2196F3", sort_order=3)
            db.add_all([cat_hair, cat_nails, cat_skin])
            await db.flush()

            # Services
            services_data = [
                Service(business_id=glow.id, category_id=cat_hair.id, name="Haircut", price=500,
                        tax_rate=18, duration_minutes=45, buffer_after_minutes=15, is_active=True, online_booking_enabled=True),
                Service(business_id=glow.id, category_id=cat_hair.id, name="Hair Color", price=1500,
                        tax_rate=18, duration_minutes=90, buffer_after_minutes=15, is_active=True, online_booking_enabled=True),
                Service(business_id=glow.id, category_id=cat_hair.id, name="Blowout", price=800,
                        tax_rate=18, duration_minutes=60, buffer_after_minutes=10, is_active=True, online_booking_enabled=True),
                Service(business_id=glow.id, category_id=cat_nails.id, name="Manicure", price=400,
                        tax_rate=18, duration_minutes=45, is_active=True, online_booking_enabled=True),
                Service(business_id=glow.id, category_id=cat_nails.id, name="Pedicure", price=500,
                        tax_rate=18, duration_minutes=60, is_active=True, online_booking_enabled=True),
                Service(business_id=glow.id, category_id=cat_skin.id, name="Facial", price=1200,
                        tax_rate=18, duration_minutes=60, buffer_after_minutes=10, is_active=True, online_booking_enabled=True),
            ]
            db.add_all(services_data)
            await db.flush()

            # Staff
            staff1 = Staff(
                business_id=glow.id, branch_id=glow_branch.id, user_id=staff_user.id,
                first_name="Alex", last_name="Thompson", email="staff@glowstudio.com",
                title="Senior Stylist", bookable=True, status="ACTIVE",
            )
            staff2 = Staff(
                business_id=glow.id, branch_id=glow_branch.id,
                first_name="Nina", last_name="Patel", email="nina@glowstudio.com",
                title="Nail Artist", bookable=True, status="ACTIVE",
            )
            db.add_all([staff1, staff2])
            await db.flush()

            # Staff role
            staff_role = roles[RoleEnum.STAFF.value]
            ur2 = UserRole(user_id=staff_user.id, role_id=staff_role.id, business_id=glow.id)
            db.add(ur2)

            # Assign services to staff
            for svc in services_data[:3]:  # Alex does hair
                db.add(StaffServiceModel(staff_id=staff1.id, service_id=svc.id))
            for svc in services_data[3:]:  # Nina does nails + skin
                db.add(StaffServiceModel(staff_id=staff2.id, service_id=svc.id))
            await db.flush()

            # Staff working hours
            for s in [staff1, staff2]:
                for day in range(7):
                    db.add(WorkingHours(
                        entity_type="staff", entity_id=s.id, business_id=glow.id,
                        day_of_week=day, is_open=day < 6,
                        open_time="09:00" if day < 6 else None,
                        close_time="19:00" if day < 6 else None,
                    ))
            await db.flush()

            # Subscription
            sub = Subscription(
                business_id=glow.id, plan_id=plans[PlanTier.PROFESSIONAL].id,
                status=SubscriptionStatus.ACTIVE, billing_cycle=BillingCycle.MONTHLY,
                start_date=datetime.now(timezone.utc),
            )
            db.add(sub)

            # Sample appointments
            now = datetime.now(timezone.utc)
            tomorrow_10am = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
            appt1 = Appointment(
                business_id=glow.id, branch_id=glow_branch.id,
                customer_id=customer.id,
                start_time=tomorrow_10am,
                end_time=tomorrow_10am + timedelta(minutes=60),
                status=AppointmentStatus.CONFIRMED,
                subtotal=500.0, tax_amount=90.0, total_amount=590.0,
            )
            db.add(appt1)
            await db.flush()
            item1 = AppointmentItem(
                appointment_id=appt1.id, service_id=services_data[0].id,
                staff_id=staff1.id, service_name="Haircut",
                duration_minutes=45, price=500, tax_rate=18,
                start_time=tomorrow_10am, end_time=tomorrow_10am + timedelta(minutes=45),
            )
            db.add(item1)

            # Past completed appointment
            past = now - timedelta(days=7)
            past_appt = Appointment(
                business_id=glow.id, branch_id=glow_branch.id,
                customer_id=customer.id,
                start_time=past, end_time=past + timedelta(minutes=60),
                status=AppointmentStatus.COMPLETED,
                subtotal=1500.0, tax_amount=270.0, total_amount=1770.0,
            )
            db.add(past_appt)
            await db.flush()
            item2 = AppointmentItem(
                appointment_id=past_appt.id, service_id=services_data[1].id,
                staff_id=staff1.id, service_name="Hair Color",
                duration_minutes=90, price=1500, tax_rate=18,
                start_time=past, end_time=past + timedelta(minutes=90),
            )
            db.add(item2)

            # Payment for past appointment
            payment = Payment(
                business_id=glow.id, appointment_id=past_appt.id,
                customer_id=customer.id, amount=1770.0, currency="INR",
                provider=PaymentProvider.MOCK, status=PaymentStatus.CAPTURED,
                provider_payment_id="mock_pay_seed001",
                paid_at=past + timedelta(minutes=90),
            )
            db.add(payment)
            await db.flush()

        # ── Business 2: Urban Cuts ────────────────────────────────────────────
        print("  Creating Business 2: Urban Cuts...")
        existing_biz2 = (await db.execute(select(Business).where(Business.slug == "urban-cuts"))).scalar_one_or_none()
        if not existing_biz2:
            urban = Business(
                owner_id=owner2_user.id, name="Urban Cuts", slug="urban-cuts",
                category=BusinessCategory.BARBER,
                description="Trendy barbershop for the modern man.",
                email="hello@urbancuts.com", phone="+91 98765 11111",
                status=BusinessStatus.ACTIVE, is_verified=True,
                subscription_plan_id=plans[PlanTier.STARTER].id,
            )
            db.add(urban)
            await db.flush()

            bo_role = roles[RoleEnum.BUSINESS_OWNER.value]
            db.add(UserRole(user_id=owner2_user.id, role_id=bo_role.id, business_id=urban.id))

            urban_branch = Branch(
                business_id=urban.id, name="Main Branch", is_primary=True, is_active=True,
                address_line1="12 Barber Lane", city="Delhi", state="Delhi",
                country="India", postal_code="110001",
            )
            db.add(urban_branch)
            await db.flush()

            for day in range(7):
                db.add(WorkingHours(
                    entity_type="branch", entity_id=urban_branch.id, business_id=urban.id,
                    day_of_week=day, is_open=day != 0,
                    open_time="10:00" if day != 0 else None,
                    close_time="21:00" if day != 0 else None,
                ))

            cat_barber = ServiceCategory(business_id=urban.id, name="Cuts", color="#795548", sort_order=1)
            db.add(cat_barber)
            await db.flush()

            urban_services = [
                Service(business_id=urban.id, category_id=cat_barber.id, name="Haircut", price=300,
                        tax_rate=18, duration_minutes=30, is_active=True, online_booking_enabled=True),
                Service(business_id=urban.id, category_id=cat_barber.id, name="Beard Trim", price=150,
                        tax_rate=18, duration_minutes=20, is_active=True, online_booking_enabled=True),
                Service(business_id=urban.id, category_id=cat_barber.id, name="Haircut + Beard", price=400,
                        tax_rate=18, duration_minutes=45, is_active=True, online_booking_enabled=True),
            ]
            db.add_all(urban_services)
            await db.flush()

            urban_staff = Staff(
                business_id=urban.id, branch_id=urban_branch.id,
                first_name="Ravi", last_name="Kumar", title="Master Barber",
                bookable=True, status="ACTIVE",
            )
            db.add(urban_staff)
            await db.flush()
            for svc in urban_services:
                db.add(StaffServiceModel(staff_id=urban_staff.id, service_id=svc.id))
            for day in range(7):
                db.add(WorkingHours(
                    entity_type="staff", entity_id=urban_staff.id, business_id=urban.id,
                    day_of_week=day, is_open=day != 0,
                    open_time="10:00" if day != 0 else None,
                    close_time="20:00" if day != 0 else None,
                ))

        # ── Business 3: Serenity Spa ──────────────────────────────────────────
        print("  Creating Business 3: Serenity Spa...")
        existing_biz3 = (await db.execute(select(Business).where(Business.slug == "serenity-spa"))).scalar_one_or_none()
        if not existing_biz3:
            spa = Business(
                owner_id=owner3_user.id, name="Serenity Spa", slug="serenity-spa",
                category=BusinessCategory.SPA,
                description="Luxury spa treatments for total relaxation and wellness.",
                email="hello@serenityspa.com", phone="+91 98765 22222",
                status=BusinessStatus.ACTIVE, is_verified=True,
                subscription_plan_id=plans[PlanTier.PROFESSIONAL].id,
            )
            db.add(spa)
            await db.flush()

            bo_role = roles[RoleEnum.BUSINESS_OWNER.value]
            db.add(UserRole(user_id=owner3_user.id, role_id=bo_role.id, business_id=spa.id))

            spa_branch = Branch(
                business_id=spa.id, name="Main Branch", is_primary=True, is_active=True,
                address_line1="88 Wellness Road", city="Bangalore", state="Karnataka",
                country="India", postal_code="560001",
            )
            db.add(spa_branch)
            await db.flush()

            for day in range(7):
                db.add(WorkingHours(
                    entity_type="branch", entity_id=spa_branch.id, business_id=spa.id,
                    day_of_week=day, is_open=True,
                    open_time="09:00", close_time="21:00",
                ))

            cat_massage = ServiceCategory(business_id=spa.id, name="Massage", color="#4CAF50", sort_order=1)
            cat_facial = ServiceCategory(business_id=spa.id, name="Facials", color="#FF9800", sort_order=2)
            db.add_all([cat_massage, cat_facial])
            await db.flush()

            spa_services = [
                Service(business_id=spa.id, category_id=cat_massage.id, name="Swedish Massage", price=2000,
                        tax_rate=18, duration_minutes=60, buffer_after_minutes=15, is_active=True, online_booking_enabled=True),
                Service(business_id=spa.id, category_id=cat_massage.id, name="Deep Tissue Massage", price=2500,
                        tax_rate=18, duration_minutes=90, buffer_after_minutes=15, is_active=True, online_booking_enabled=True),
                Service(business_id=spa.id, category_id=cat_facial.id, name="Hydrating Facial", price=1800,
                        tax_rate=18, duration_minutes=75, buffer_after_minutes=10, is_active=True, online_booking_enabled=True),
                Service(business_id=spa.id, category_id=cat_facial.id, name="Anti-Aging Treatment", price=3500,
                        tax_rate=18, duration_minutes=90, buffer_after_minutes=15, is_active=True, online_booking_enabled=True),
            ]
            db.add_all(spa_services)
            await db.flush()

            for i, name in enumerate(["Meera Singh", "Deepa Nair"]):
                first, last = name.split()
                s = Staff(
                    business_id=spa.id, branch_id=spa_branch.id,
                    first_name=first, last_name=last, title="Therapist",
                    bookable=True, status="ACTIVE",
                )
                db.add(s)
                await db.flush()
                for svc in spa_services:
                    db.add(StaffServiceModel(staff_id=s.id, service_id=svc.id))
                for day in range(7):
                    db.add(WorkingHours(
                        entity_type="staff", entity_id=s.id, business_id=spa.id,
                        day_of_week=day, is_open=True,
                        open_time="09:00", close_time="21:00",
                    ))

        await db.commit()
        print("\n✅ Seed complete!")
        print("\n📋 Demo Credentials:")
        print("  Platform Admin : admin@zenglow.com / Admin@1234")
        print("  Business Owner : owner@glowstudio.com / Owner@1234")
        print("  Staff          : staff@glowstudio.com / Staff@1234")
        print("  Customer       : customer@example.com / Customer@1234")
        print("\n🏢 Businesses: Glow Studio, Urban Cuts, Serenity Spa")


if __name__ == "__main__":
    asyncio.run(seed())
