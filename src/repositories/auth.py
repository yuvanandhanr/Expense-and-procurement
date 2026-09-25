import uuid
from typing import Optional
from sqlalchemy import select
from src.models.auth import User, Role, Permission, UserRole, LoginSession, LoginHistory, RefreshToken, VendorUser, OTPRequest
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Data access repository for User entities.
    """

    def __init__(self, session) -> None:
        super().__init__(User, session)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieves a user by their integer primary key, eagerly loading roles.
        """
        from sqlalchemy.orm import selectinload
        query = select(User).options(selectinload(User.roles)).where(User.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieves a user by their email address.
        """
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_supabase_uid(self, uid: uuid.UUID) -> Optional[User]:
        """
        Retrieves a user by their Supabase UUID reference.
        """
        query = select(User).where(User.supabase_uid == uid)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """
        Retrieves a user by their Google OAuth sub ID.
        """
        query = select(User).where(User.google_id == google_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class RoleRepository(BaseRepository[Role]):
    """
    Data access repository for Role entities.
    """

    def __init__(self, session) -> None:
        super().__init__(Role, session)

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        """
        Retrieves a role by its integer primary key.
        """
        return await self.session.get(Role, role_id)

    async def get_by_name(self, name: str) -> Optional[Role]:
        """
        Retrieves a role by its unique name.
        """
        query = select(Role).where(Role.role_name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class PermissionRepository(BaseRepository[Permission]):
    """
    Data access repository for Permission entities.
    """

    def __init__(self, session) -> None:
        super().__init__(Permission, session)

    async def get_by_id(self, permission_id: int) -> Optional[Permission]:
        """
        Retrieves a permission by its integer primary key.
        """
        return await self.session.get(Permission, permission_id)

    async def get_by_name(self, name: str) -> Optional[Permission]:
        """
        Retrieves a permission by its unique name code.
        """
        query = select(Permission).where(Permission.permission_name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class UserRoleRepository(BaseRepository[UserRole]):
    """
    Data access repository for User-Role associations.
    """

    def __init__(self, session) -> None:
        super().__init__(UserRole, session)

    async def get_by_id(self, user_role_id: int) -> Optional[UserRole]:
        """
        Retrieves an association record by its primary key.
        """
        return await self.session.get(UserRole, user_role_id)

    async def get_by_user_and_role(self, user_id: int, role_id: int) -> Optional[UserRole]:
        """
        Retrieves an association by specific user and role keys.
        """
        query = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class SessionRepository(BaseRepository[LoginSession]):
    """
    Data access repository for User Login Session auditing.
    """

    def __init__(self, session) -> None:
        super().__init__(LoginSession, session)

    async def get_by_id(self, session_id: int) -> Optional[LoginSession]:
        """
        Retrieves a session audit record by its primary key.
        """
        return await self.session.get(LoginSession, session_id)

    async def get_active_session_by_token(self, token: str) -> Optional[LoginSession]:
        """
        Retrieves an active session matching the provided JWT token.
        """
        query = select(LoginSession).where(
            LoginSession.jwt_token == token,
            LoginSession.status == "Active"
        )
        result = await self.session.execute(query)
        return result.scalars().first()


class LoginHistoryRepository(BaseRepository[LoginHistory]):
    """
    Data access repository for User Login History auditing.
    """
    def __init__(self, session) -> None:
        super().__init__(LoginHistory, session)

    async def get_by_id(self, history_id: int) -> Optional[LoginHistory]:
        """
        Retrieves a login history record by its primary key.
        """
        return await self.session.get(LoginHistory, history_id)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """
    Data access repository for User Refresh Tokens.
    """
    def __init__(self, session) -> None:
        super().__init__(RefreshToken, session)

    async def get_by_id(self, token_id: int) -> Optional[RefreshToken]:
        """
        Retrieves a refresh token by primary key.
        """
        return await self.session.get(RefreshToken, token_id)

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """
        Retrieves a refresh token record matching the unique token string.
        """
        query = select(RefreshToken).where(
            RefreshToken.token == token,
            RefreshToken.is_expired == False,
            RefreshToken.revoked_at == None
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class VendorUserRepository(BaseRepository[VendorUser]):
    """
    Data access repository for Vendor User mappings.
    """

    def __init__(self, session) -> None:
        super().__init__(VendorUser, session)

    async def get_by_id(self, vendor_user_id: int) -> Optional[VendorUser]:
        return await self.session.get(VendorUser, vendor_user_id)

    async def get_by_user_id(self, user_id: int) -> Optional[VendorUser]:
        query = select(VendorUser).where(VendorUser.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_vendor_id(self, vendor_id: int) -> list[VendorUser]:
        query = select(VendorUser).where(VendorUser.vendor_id == vendor_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class OTPRequestRepository(BaseRepository[OTPRequest]):
    """
    Data access repository for OTP Requests.
    """

    def __init__(self, session) -> None:
        super().__init__(OTPRequest, session)

    async def get_by_id(self, request_id: int) -> Optional[OTPRequest]:
        return await self.session.get(OTPRequest, request_id)

    async def get_active_by_email(self, email: str) -> Optional[OTPRequest]:
        # Return the latest active OTP request for this email
        query = (
            select(OTPRequest)
            .where(OTPRequest.email == email)
            .order_by(OTPRequest.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
