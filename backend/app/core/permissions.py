"""
Permission constants and role-permission mapping.
Rather than hardcoding checks in controllers, define permissions here
and assign them to roles. Services check permissions at the service layer.
"""
from typing import Dict, List, Set

from app.models.user import RoleEnum


class Permission:
    # Business
    BUSINESS_READ = "business.read"
    BUSINESS_CREATE = "business.create"
    BUSINESS_UPDATE = "business.update"
    BUSINESS_DELETE = "business.delete"

    # Branch
    BRANCH_READ = "branch.read"
    BRANCH_CREATE = "branch.create"
    BRANCH_UPDATE = "branch.update"
    BRANCH_DELETE = "branch.delete"

    # Staff
    STAFF_READ = "staff.read"
    STAFF_CREATE = "staff.create"
    STAFF_UPDATE = "staff.update"
    STAFF_DELETE = "staff.delete"

    # Services
    SERVICE_READ = "service.read"
    SERVICE_CREATE = "service.create"
    SERVICE_UPDATE = "service.update"
    SERVICE_DELETE = "service.delete"

    # Customer (CRM)
    CUSTOMER_READ = "customer.read"
    CUSTOMER_UPDATE = "customer.update"

    # Bookings
    BOOKING_CREATE = "booking.create"
    BOOKING_READ = "booking.read"
    BOOKING_UPDATE = "booking.update"
    BOOKING_CANCEL = "booking.cancel"

    # Payments
    PAYMENT_READ = "payment.read"
    PAYMENT_REFUND = "payment.refund"

    # Reports
    REPORTS_READ = "reports.read"

    # Platform Admin
    ADMIN_BUSINESSES = "admin.businesses"
    ADMIN_USERS = "admin.users"
    ADMIN_REPORTS = "admin.reports"
    ADMIN_SUBSCRIPTIONS = "admin.subscriptions"


# Role → Permission mapping
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    RoleEnum.PLATFORM_ADMIN.value: {
        Permission.BUSINESS_READ, Permission.BUSINESS_UPDATE, Permission.BUSINESS_DELETE,
        Permission.ADMIN_BUSINESSES, Permission.ADMIN_USERS,
        Permission.ADMIN_REPORTS, Permission.ADMIN_SUBSCRIPTIONS,
        Permission.REPORTS_READ,
        Permission.BOOKING_READ,
        Permission.PAYMENT_READ, Permission.PAYMENT_REFUND,
    },
    RoleEnum.BUSINESS_OWNER.value: {
        Permission.BUSINESS_READ, Permission.BUSINESS_UPDATE,
        Permission.BRANCH_READ, Permission.BRANCH_CREATE,
        Permission.BRANCH_UPDATE, Permission.BRANCH_DELETE,
        Permission.STAFF_READ, Permission.STAFF_CREATE,
        Permission.STAFF_UPDATE, Permission.STAFF_DELETE,
        Permission.SERVICE_READ, Permission.SERVICE_CREATE,
        Permission.SERVICE_UPDATE, Permission.SERVICE_DELETE,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_UPDATE,
        Permission.BOOKING_CREATE, Permission.BOOKING_READ,
        Permission.BOOKING_UPDATE, Permission.BOOKING_CANCEL,
        Permission.PAYMENT_READ, Permission.PAYMENT_REFUND,
        Permission.REPORTS_READ,
    },
    RoleEnum.BUSINESS_MANAGER.value: {
        Permission.BUSINESS_READ,
        Permission.BRANCH_READ, Permission.BRANCH_UPDATE,
        Permission.STAFF_READ, Permission.STAFF_CREATE, Permission.STAFF_UPDATE,
        Permission.SERVICE_READ, Permission.SERVICE_CREATE, Permission.SERVICE_UPDATE,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_UPDATE,
        Permission.BOOKING_CREATE, Permission.BOOKING_READ,
        Permission.BOOKING_UPDATE, Permission.BOOKING_CANCEL,
        Permission.PAYMENT_READ,
        Permission.REPORTS_READ,
    },
    RoleEnum.STAFF.value: {
        Permission.BUSINESS_READ,
        Permission.BRANCH_READ,
        Permission.SERVICE_READ,
        Permission.CUSTOMER_READ,
        Permission.BOOKING_READ, Permission.BOOKING_UPDATE,
        Permission.PAYMENT_READ,
    },
    RoleEnum.RECEPTIONIST.value: {
        Permission.BUSINESS_READ,
        Permission.BRANCH_READ,
        Permission.SERVICE_READ,
        Permission.CUSTOMER_READ, Permission.CUSTOMER_UPDATE,
        Permission.BOOKING_CREATE, Permission.BOOKING_READ,
        Permission.BOOKING_UPDATE, Permission.BOOKING_CANCEL,
        Permission.PAYMENT_READ,
    },
    RoleEnum.CUSTOMER.value: {
        Permission.BOOKING_CREATE, Permission.BOOKING_READ, Permission.BOOKING_CANCEL,
        Permission.PAYMENT_READ,
    },
}


def has_permission(role_name: str, permission: str) -> bool:
    """Check if a role has a given permission."""
    return permission in ROLE_PERMISSIONS.get(role_name, set())


def get_permissions_for_roles(role_names: List[str]) -> Set[str]:
    """Aggregate permissions for a set of role names."""
    perms: Set[str] = set()
    for name in role_names:
        perms |= ROLE_PERMISSIONS.get(name, set())
    return perms
