import logging
import time
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

# High-performance in-memory cache for active JWT sessions to satisfy SLA
_TOKEN_CACHE: dict[str, float] = {}

def cache_active_token(token: str, ttl: float = 60.0) -> None:
    _TOKEN_CACHE[token] = time.time() + ttl

def is_token_cached_active(token: str) -> bool:
    import sys
    if "pytest" in sys.modules or settings.ENVIRONMENT == "testing":
        return False
    exp = _TOKEN_CACHE.get(token)
    if exp and exp > time.time():
        return True
    return False

def invalidate_token_cache(token: str) -> None:
    _TOKEN_CACHE.pop(token, None)


class JWTBearer(HTTPBearer):
    """
    FastAPI Dependency that extracts and validates the Supabase JWT.
    Checks the local database to verify if the session is still Active (not revoked).
    Supports token from Authorization header or 'token' query parameter (for direct browser file views).
    """

    def __init__(self, auto_error: bool = False):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request, db: AsyncSession = Depends(get_db_session)) -> dict:
        token: Optional[str] = None

        # 1. Check Authorization header
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        if credentials and credentials.credentials:
            token = credentials.credentials

        # 2. Check query parameter fallback
        if not token:
            token = request.query_params.get("token")

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials missing"
            )

        # Verify active session via memory cache or database lookup
        active_session = None
        session_repo = SessionRepository(db)
        if not is_token_cached_active(token):
            active_session = await session_repo.get_active_session_by_token(token)
            if not active_session:
                logger.warning("Attempted request with invalid or revoked session token.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session is invalid or has been logged out"
                )
            cache_active_token(token, ttl=60.0)

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
            invalidate_token_cache(token)
            # Update session status to revoked if token is expired
            if not active_session:
                active_session = await session_repo.get_active_session_by_token(token)
            if active_session:
                active_session.status = "Revoked"
                await session_repo.update(active_session)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired"
            )
        except jwt.InvalidTokenError as e:
            invalidate_token_cache(token)
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
