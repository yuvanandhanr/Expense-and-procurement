import logging
import uuid
import jwt
from typing import List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.database.dependency import get_db_session
from src.models.auth import User, LoginSession
from src.repositories.auth import UserRepository, SessionRepository

logger = logging.getLogger(__name__)


class JWTBearer(HTTPBearer):
    """
    FastAPI Dependency that extracts and validates the Supabase JWT.
    Checks the local database to verify if the session is still Active (not revoked).
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request, db: AsyncSession = Depends(get_db_session)) -> dict:
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials missing"
            )

        token = credentials.credentials

        # Verify active session in local database
        session_repo = SessionRepository(db)
        active_session = await session_repo.get_active_session_by_token(token)
        if not active_session:
            logger.warning("Attempted request with invalid or revoked session token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session is invalid or has been logged out"
            )

        try:
            # Decode the Supabase JWT
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}  # Disable audience check for flexible environments
            )
            # Store token in request state for downstream use if needed (e.g. logout)
            request.state.access_token = token
            return payload
        except jwt.ExpiredSignatureError:
            # Update session status to revoked if token is expired
            active_session.status = "Revoked"
            await session_repo.update(active_session)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token signature or payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )


async def get_current_user(
    payload: dict = Depends(JWTBearer()),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Resolves the local User profile matching the sub identifier (ID or UUID) from the JWT payload.
    """
    sub_claim = payload.get("sub")
    if not sub_claim:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier"
        )

    user_repo = UserRepository(db)
    user = None

    try:
        user_id = int(sub_claim)
        user = await user_repo.get_by_id(user_id)
    except ValueError:
        try:
            supabase_uid = uuid.UUID(sub_claim)
            user = await user_repo.get_by_supabase_uid(supabase_uid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid subject format"
            )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not registered in local database"
        )

    if user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


class RoleChecker:
    """
    Dependency checking user roles dynamically.
    """
    def __init__(self, required_roles: List[str]) -> None:
        self.required_roles = required_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_roles = {role.role_name for role in current_user.roles if role.status}
        if "Admin" not in user_roles and not any(req_role in user_roles for req_role in self.required_roles):
            logger.warning(
                f"User {current_user.email} (ID: {current_user.user_id}) denied access. "
                f"Requires one of roles: {self.required_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        return current_user


class PermissionChecker:
    """
    Dependency checking user permissions dynamically from the loaded roles and permissions.
    """

    def __init__(self, required_permission: str) -> None:
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        # Check active permissions across all user's active roles
        user_permissions = set()
        is_admin = False
        for role in current_user.roles:
            if not role.status:
                continue
            if role.role_name == "Admin":
                is_admin = True
            for perm in role.permissions:
                user_permissions.add(perm.permission_name)

        if not is_admin and self.required_permission not in user_permissions:
            logger.warning(
                f"User {current_user.email} (ID: {current_user.user_id}) denied access. "
                f"Missing required permission: '{self.required_permission}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )

        return current_user
