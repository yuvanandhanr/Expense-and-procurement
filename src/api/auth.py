from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import get_current_user, PermissionChecker
from src.database.dependency import get_db_session
from src.models.auth import User
from src.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    CurrentUser,
    ErrorResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GoogleLoginRequest,
    VendorOTPRequest,
    VendorOTPVerify,
)
from pydantic import BaseModel
from src.services.auth_service import AuthenticationService

class MFASetupResponse(BaseModel):
    secret: str
    uri: str

class MFAEnableRequest(BaseModel):
    otp: str

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        404: {"model": ErrorResponse, "description": "User profile not found in local system"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Authenticates a user against local credentials.
    Associates the login session locally and records client IP and User-Agent details.
    """
    auth_service = AuthenticationService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.login(body, ip=ip_address, user_agent=user_agent)


@router.post(
    "/google",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Google credential or domain unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def google_login(
    request: Request,
    body: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Authenticates a user using Google Sign-In ID Token credentials.
    """
    auth_service = AuthenticationService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.google_login(body.credential, ip=ip_address, user_agent=user_agent)


@router.post(
    "/vendor/otp-request",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid vendor email"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def request_vendor_otp(
    body: VendorOTPRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Validates the vendor email address and triggers a 6-digit verification OTP.
    """
    auth_service = AuthenticationService(db)
    result = await auth_service.request_vendor_otp(body.email)
    return result


@router.post(
    "/vendor/otp-verify",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid/expired OTP"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def verify_vendor_otp(
    request: Request,
    body: VendorOTPVerify,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Verifies the 6-digit OTP code and generates authentication tokens for the vendor.
    """
    auth_service = AuthenticationService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.verify_vendor_otp(body.email, body.otp, ip=ip_address, user_agent=user_agent)

@router.post(
    "/vendor/mfa/setup",
    response_model=MFASetupResponse,
    dependencies=[Depends(get_current_user)]
)
async def setup_vendor_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generates a new TOTP secret and provisioning URI for the vendor.
    """
    auth_service = AuthenticationService(db)
    return await auth_service.setup_vendor_mfa(current_user.email)

@router.post(
    "/vendor/mfa/enable",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)]
)
async def enable_vendor_mfa(
    body: MFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Verifies the first TOTP code and enables MFA for the vendor.
    """
    auth_service = AuthenticationService(db)
    return await auth_service.enable_vendor_mfa(current_user.email, body.otp)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated or session revoked"}
    }
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Terminates the active session and invalidates the authentication token.
    """
    access_token = getattr(request.state, "access_token", None)
    if access_token:
        auth_service = AuthenticationService(db)
        await auth_service.logout(access_token)
        
    return {"message": "Successfully logged out"}


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Obtains a new access token using a valid refresh token.
    """
    auth_service = AuthenticationService(db)
    return await auth_service.refresh(body.refresh_token)


@router.get(
    "/me",
    response_model=CurrentUser,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "User profile not found"}
    }
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's details, including assigned roles and permissions.
    """
    return current_user


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Initiates password reset process and generates a verification token.
    """
    auth_service = AuthenticationService(db)
    token = await auth_service.forgot_password(body.email)
    return {"message": "Password reset token generated", "token": token}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resets user password with the verification token.
    """
    auth_service = AuthenticationService(db)
    await auth_service.reset_password(body.token, body.new_password)
    return {"message": "Password reset successfully"}


@router.get(
    "/active-sessions",
    dependencies=[Depends(PermissionChecker("admin.settings"))]
)
async def get_active_sessions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Returns list of active login sessions.
    """
    from sqlalchemy import select
    from src.models.auth import LoginSession
    query = select(LoginSession).where(LoginSession.status == "Active").offset(skip).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()
    return [
        {
            "session_id": s.session_id,
            "user_id": s.user_id,
            "login_time": s.login_time,
            "ip_address": s.ip_address,
            "device_name": s.device_name,
            "browser": s.browser,
            "status": s.status
        }
        for s in sessions
    ]


@router.get(
    "/login-history",
    dependencies=[Depends(PermissionChecker("admin.settings"))]
)
async def get_login_history(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Returns login attempts audit history.
    """
    from sqlalchemy import select
    from src.models.auth import LoginHistory
    query = select(LoginHistory).order_by(LoginHistory.login_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    history = result.scalars().all()
    return [
        {
            "history_id": h.history_id,
            "user_id": h.user_id,
            "email": h.email,
            "login_time": h.login_time,
            "ip_address": h.ip_address,
            "user_agent": h.user_agent,
            "status": h.status,
            "failure_reason": h.failure_reason
        }
        for h in history
    ]
