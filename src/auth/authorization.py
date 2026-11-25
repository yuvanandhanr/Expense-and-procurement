from typing import Optional
from src.models.auth import User


def is_amount_visible(user: Optional[User]) -> bool:
    """
    Role-Based Amount Visibility:
    Admin, Finance Manager, CEO, CFO, and SuperAdmin can view organization-wide monetary amounts.
    """
    if not user or not getattr(user, "roles", None):
        return False
    user_roles = [r.role_name for r in user.roles]
    allowed_roles = {"Admin", "Finance Manager", "SuperAdmin", "CEO", "CFO"}
    return bool(allowed_roles.intersection(user_roles))
