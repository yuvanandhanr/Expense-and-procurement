from typing import Optional
from src.models.auth import User


def is_amount_visible(user: Optional[User]) -> bool:
    """
    Role-Based Amount Visibility:
    Only Admin and Finance Manager should be able to view monetary amounts.
    Hide all amount-related fields from Employees, Managers, Vendors, CFO, and CEO.
    """
    if not user or not getattr(user, "roles", None):
        return False
    user_roles = [r.role_name for r in user.roles]
    # Allowed: Admin, Finance Manager, SuperAdmin
    allowed_roles = {"Admin", "Finance Manager", "SuperAdmin"}
    return bool(allowed_roles.intersection(user_roles))
