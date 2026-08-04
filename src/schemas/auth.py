import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Validation schema for authentication request.
    """
    email: EmailStr = Field(..., description="User login email address")
    password: str = Field(..., description="User login password")


class TokenResponse(BaseModel):
    """
    Serialization schema for access token and refresh token details.
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token used to obtain a new access token")
    token_type: str = Field("bearer", description="Token transmission type")
    expires_in: int = Field(..., description="Duration of access token validity in seconds")


class RefreshRequest(BaseModel):
    """
    Validation schema for token refresh request.
    """
    refresh_token: str = Field(..., description="Active refresh token")


class PermissionSchema(BaseModel):
    """
    Serialization schema for permissions.
    """
    model_config = ConfigDict(from_attributes=True)

    permission_id: int
    permission_name: str
    module_name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class RoleSchema(BaseModel):
    """
    Serialization schema for roles including nested permissions.
    """
    model_config = ConfigDict(from_attributes=True)

    role_id: int
    role_name: str
    description: Optional[str] = None
    status: bool
    created_at: datetime
    permissions: List[PermissionSchema] = []


class CurrentUser(BaseModel):
    """
    Serialization schema representing the currently authenticated user.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    supabase_uid: Optional[uuid.UUID] = None
    employee_code: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    designation: Optional[str] = None
    designation_id: Optional[int] = None
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    employment_type: str = "Full-Time"
    status: str = "Active"
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    roles: List[RoleSchema] = []


class SessionSchema(BaseModel):
    """
    Serialization schema representing a user login session record.
    """
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    user_id: int
    login_time: datetime
    logout_time: Optional[datetime] = None
    ip_address: Optional[str] = None
    device_name: Optional[str] = None
    browser: Optional[str] = None
    status: str


class ErrorResponse(BaseModel):
    """
    Standard schema for HTTP error responses.
    """
    detail: str = Field(..., description="Detailed description of the error")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to receive password reset request")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Reset token received via email")
    new_password: str = Field(..., min_length=8, description="New password")


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., description="Current active password")
    new_password: str = Field(..., min_length=8, description="New password to set")


class UserCreate(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=100)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8, description="Raw initial password")
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    designation_id: Optional[int] = None
    designation: Optional[str] = None
    employment_type: Optional[str] = "Full-Time"
    status: Optional[str] = "Active"
    role_ids: Optional[List[int]] = []


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, description="New password if resetting")
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    designation_id: Optional[int] = None
    designation: Optional[str] = None
    employment_type: Optional[str] = None
    status: Optional[str] = None
    role_ids: Optional[List[int]] = None


class RoleCreate(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[bool] = True
    permission_ids: Optional[List[int]] = []


class RoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class PermissionCreate(BaseModel):
    permission_name: str = Field(..., min_length=1, max_length=255)
    module_name: Optional[str] = None
    description: Optional[str] = None
