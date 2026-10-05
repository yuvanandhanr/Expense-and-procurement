from datetime import timezone, datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.dependencies import PermissionChecker, get_current_user
from src.database.dependency import get_db_session
from src.models.auth import User
from src.schemas.auth import CurrentUser, ErrorResponse, UserCreate, UserUpdate
from src.services.auth_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=CurrentUser,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "User profile not found"}
    }
)
async def get_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the current user's profile.
    """
    return current_user


@router.get(
    "",
    response_model=List[CurrentUser],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"}
    }
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("users.view"))
):
    """
    Lists all users in the system.
    """
    service = UserService(db)
    return await service.list_users(skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=CurrentUser,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("users.view"))
):
    """
    Retrieves a single user's profile details.
    """
    service = UserService(db)
    return await service.get_user(user_id)


@router.post(
    "",
    response_model=CurrentUser,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "User already exists"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"}
    }
)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("users.create"))
):
    """
    Creates a new user account locally.
    """
    is_admin = any(role.role_name == "Admin" for role in current_user.roles)
    if not is_admin:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only Admins can add users."
        )
    service = UserService(db)
    return await service.create_user(data)


@router.put(
    "/{user_id}",
    response_model=CurrentUser,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("users.update"))
):
    """
    Updates an existing user's profile details or role assignments.
    """
    is_admin = any(role.role_name == "Admin" for role in current_user.roles)
    if not is_admin:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only Admins can edit or manage users."
        )
    if data.department_name is not None and data.department_name != "":
        from sqlalchemy import select
        from src.models.organization import Department
        res = await db.execute(select(Department.department_name, Department.department_id))
        dept_map = {r[0]: r[1] for r in res.all()}
        if data.department_name not in dept_map:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid department name.")
        data.department_id = dept_map[data.department_name]
            
    if data.employee_type is not None and data.employee_type != "":
        allowed_types = ["Intern", "Consultant", "Full-Time", "Part-Time", "Contract"]
        if data.employee_type not in allowed_types:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid employee type.")

    service = UserService(db)
    
    if data.role_ids is not None:
        allowed_roles = [
            "Employee", "Manager", "Finance", "Admin", "CFO", 
            "Finance Manager", "CEO", "Intern", "Pending Assignment", 
            "Vendor Portal", "Operations", "Sales & Marketing", "Administration"
        ]
        
    return await service.update_user(user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "User not found"}
    }
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(PermissionChecker("users.delete"))
):
    """
    Soft-deletes (deactivates) a user account.
    """
    is_admin = any(role.role_name == "Admin" for role in current_user.roles)
    if not is_admin:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only Admins can delete users."
        )
    service = UserService(db)
    await service.delete_user(user_id)


@router.post(
    "/{user_id}/lock",
    response_model=CurrentUser,
    dependencies=[Depends(PermissionChecker("admin.settings"))]
)
async def lock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Locks an employee account manually.
    """
    is_admin = any(role.role_name == "Admin" for role in current_user.roles)
    if not is_admin:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only Admins can lock users."
        )
    service = UserService(db)
    user = await service.get_user(user_id)
    user.is_locked = True
    user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=365)
    await service.user_repo.update(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/{user_id}/unlock",
    response_model=CurrentUser,
    dependencies=[Depends(PermissionChecker("admin.settings"))]
)
async def unlock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Unlocks an employee account manually.
    """
    is_admin = any(role.role_name == "Admin" for role in current_user.roles)
    if not is_admin:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403, 
            detail="Only Admins can unlock users."
        )
    service = UserService(db)
    user = await service.get_user(user_id)
    user.is_locked = False
    user.failed_login_attempts = 0
    user.locked_until = None
    await service.user_repo.update(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/{user_id}/reset-sessions",
    dependencies=[Depends(PermissionChecker("admin.settings"))]
)
async def reset_user_sessions(
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Revokes all active login sessions and refresh tokens for a user.
    """
    from sqlalchemy import update
    from src.models.auth import LoginSession, RefreshToken
    
    # Revoke sessions
    session_update = (
        update(LoginSession)
        .where(LoginSession.user_id == user_id, LoginSession.status == "Active")
        .values(status="Revoked", logout_time=datetime.utcnow())
    )
    await db.execute(session_update)
    
    # Revoke refresh tokens
    token_update = (
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.is_expired == False)
        .values(is_expired=True, revoked_at=datetime.utcnow())
    )
    await db.execute(token_update)
    
    return {"detail": "All active sessions for this user have been successfully reset."}
