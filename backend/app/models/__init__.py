"""
Import all models here so Alembic can discover them.
"""
from app.models.user import User, Role, Permission, UserRole, RolePermission  # noqa: F401
from app.models.business import Business, Branch  # noqa: F401
from app.models.staff import Staff, StaffService, WorkingHours, StaffLeave  # noqa: F401
from app.models.service import Service, ServiceCategory  # noqa: F401
from app.models.customer import Customer, FavouriteBusiness  # noqa: F401
from app.models.appointment import Appointment, AppointmentItem  # noqa: F401
from app.models.payment import Payment, Refund, Invoice  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.subscription import Subscription, SubscriptionPlan  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.resource import Resource  # noqa: F401
from app.models.inventory import ProductCategory, Product, StockMovement  # noqa: F401
from app.models.membership import MembershipPlan, CustomerMembership  # noqa: F401
from app.models.package import PackageTemplate, PackageItemTemplate, CustomerPackage, CustomerPackageItem  # noqa: F401
from app.models.gift_card import GiftCard, GiftCardTransaction  # noqa: F401
from app.models.pos import Order, OrderItem, OrderPayment  # noqa: F401
