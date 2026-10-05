import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base

if TYPE_CHECKING:
    from src.models.organization import Department, Designation, CostCenter, BudgetCode
    from src.models.vendor import Vendor


class User(Base):
    """
    SQLAlchemy Model for the public.users table.
    """
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for local user"
    )
    supabase_uid: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=True, comment="Supabase authenticated user UUID reference"
    )
    employee_code: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Unique business employee code"
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="User first name"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="User last name"
    )
    email: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Unique user email address"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="User telephone contact"
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Optional hashed password for non-auth logins"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("departments.department_id"), nullable=True, comment="Foreign key referencing department"
    )
    cost_center_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("cost_centres.cost_center_id"), nullable=True, comment="Foreign key referencing cost center"
    )
    budget_code_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("budget_codes.budget_code_id"), nullable=True, comment="Foreign key referencing budget code"
    )
    business_unit: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Assigned business unit"
    )
    location: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Assigned location"
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True, comment="Foreign key referencing user's manager"
    )
    designation: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="User designation string"
    )
    designation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("designations.designation_id"), nullable=True, comment="Foreign key referencing designation"
    )
    employment_type: Mapped[str] = mapped_column(
        String, default="Full-Time", nullable=True, comment="Employment type"
    )
    department_name: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Department assignment (string)"
    )
    employee_type: Mapped[str] = mapped_column(
        String, default="pending assignment", nullable=True, comment="Employee type"
    )
    status: Mapped[str] = mapped_column(
        String, default="Active", nullable=True, comment="User status"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=True, comment="Number of failed login attempts"
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=True, comment="Is account locked"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Account locked until timestamp"
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Last login timestamp"
    )
    google_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, nullable=True, comment="Google OAuth sub ID"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="User profile photo URL"
    )
    login_provider: Mapped[Optional[str]] = mapped_column(
        String, default="LOCAL", nullable=True, comment="Auth provider (GOOGLE, LOCAL)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True, comment="Last updated timestamp"
    )

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="User.user_id == UserRole.user_id",
        secondaryjoin="Role.role_id == UserRole.role_id",
        back_populates="users",
        lazy="selectin"
    )
    sessions: Mapped[List["LoginSession"]] = relationship(
        "LoginSession", back_populates="user", cascade="all, delete-orphan"
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="users", foreign_keys="[User.department_id]"
    )
    cost_center: Mapped[Optional["CostCenter"]] = relationship(
        "CostCenter", back_populates="users", foreign_keys="[User.cost_center_id]"
    )
    budget_code: Mapped[Optional["BudgetCode"]] = relationship(
        "BudgetCode", foreign_keys="[User.budget_code_id]"
    )
    designation_rel: Mapped[Optional["Designation"]] = relationship(
        "Designation", back_populates="users", foreign_keys="[User.designation_id]"
    )

    @property
    def full_name(self) -> str:
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else (self.email or f"User #{self.user_id}")


class Role(Base):
    """
    SQLAlchemy Model for the public.roles table.
    """
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for roles"
    )
    role_name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Unique system role name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Role description"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=True, comment="Role status"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Creation timestamp"
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Role.role_id == UserRole.role_id",
        secondaryjoin="User.user_id == UserRole.user_id",
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles", lazy="selectin"
    )


class Permission(Base):
    """
    SQLAlchemy Model for the public.permissions table.
    """
    __tablename__ = "permissions"

    permission_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for permissions"
    )
    permission_name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Unique permission code"
    )
    module_name: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Associated software module identifier"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Permission description"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Creation timestamp"
    )

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )


class UserRole(Base):
    """
    SQLAlchemy Model for the public.user_roles mapping table.
    """
    __tablename__ = "user_roles"

    user_role_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key mapping"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True, comment="Associated user"
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.role_id"), nullable=True, comment="Associated role"
    )
    assigned_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True, comment="Admin user who assigned this role"
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Assignment timestamp"
    )


class RolePermission(Base):
    """
    SQLAlchemy Model for the public.role_permissions mapping table.
    """
    __tablename__ = "role_permissions"

    role_permission_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key mapping"
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.role_id"), nullable=True, comment="Associated role"
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("permissions.permission_id"), nullable=True, comment="Associated permission"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Mapping timestamp"
    )


class LoginSession(Base):
    """
    SQLAlchemy Model for the public.login_sessions table.
    """
    __tablename__ = "login_sessions"

    session_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for sessions"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True, comment="Associated user"
    )
    jwt_token: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Assigned JWT access token"
    )
    login_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Login timestamp"
    )
    logout_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Logout timestamp"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Client IP address"
    )
    device_name: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Client device name"
    )
    browser: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Client browser description"
    )
    status: Mapped[str] = mapped_column(
        String, default="Active", nullable=True, comment="Session status (Active/Revoked)"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")


class LoginHistory(Base):
    """
    SQLAlchemy Model for the public.login_history table.
    """
    __tablename__ = "login_history"

    history_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for login history"
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, comment="Associated user reference"
    )
    email: Mapped[str] = mapped_column(
        String, nullable=False, comment="Login email address"
    )
    login_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Login attempt timestamp"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Client IP address"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Client User-Agent details"
    )
    status: Mapped[str] = mapped_column(
        String, default="Success", nullable=True, comment="Attempt status (Success/Failed/Locked)"
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="Failure description"
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")


class RefreshToken(Base):
    """
    SQLAlchemy Model for the public.refresh_tokens table.
    """
    __tablename__ = "refresh_tokens"

    token_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for refresh tokens"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, comment="Associated user reference"
    )
    token: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Hashed or unique refresh token string"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="Token expiration timestamp"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True, comment="Token creation timestamp"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Token revocation timestamp"
    )
    is_expired: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=True, comment="Expired status flag"
    )

    # Relationships
    user: Mapped["User"] = relationship("User")


class VendorUser(Base):
    """
    SQLAlchemy Model for the public.vendor_users table mapping.
    """
    __tablename__ = "vendor_users"

    vendor_user_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for vendor user mapping"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, comment="FK referencing user"
    )
    vendor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False, comment="FK referencing vendor"
    )

    user: Mapped["User"] = relationship("User", lazy="joined")
    vendor: Mapped["Vendor"] = relationship("Vendor", lazy="joined")


class OTPRequest(Base):
    """
    SQLAlchemy Model for tracking OTP requests and validation attempts for vendors.
    """
    __tablename__ = "otp_requests"

    request_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for OTP request"
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Vendor email address requesting OTP"
    )
    otp_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Securely hashed OTP code"
    )
    attempts: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False, comment="Verification retry count"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="OTP expiration timestamp"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="Timestamp when OTP was generated"
    )

