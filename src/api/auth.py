from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import get_current_user
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
)
from src.services.auth_service import AuthenticationService

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
