from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.models.approval import ApprovalComment
from src.schemas.approval import CommentCreate, CommentSchema
from src.repositories.approval import CommentRepository
from src.api.purchase_requisitions import check_pr_access

router = APIRouter(prefix="/pr", tags=["PR Comments"])


@router.post("/{id}/comments", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(
    id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = CommentRepository(db)
    
    # Verify access to PR
    from src.repositories.purchase_requisition import PRRepository
    pr_repo = PRRepository(db)
    pr = await pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    await check_pr_access(pr, current_user, db)

    comment = ApprovalComment(
        pr_id=id,
        user_id=current_user.user_id,
        content=data.content,
        parent_comment_id=data.parent_comment_id,
        is_internal=data.is_internal,
        created_at=datetime.utcnow()
    )
    return await repo.create(comment)


@router.get("/{id}/comments", response_model=List[CommentSchema])
async def list_comments(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = CommentRepository(db)

    # Verify access to PR
    from src.repositories.purchase_requisition import PRRepository
    pr_repo = PRRepository(db)
    pr = await pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    await check_pr_access(pr, current_user, db)

    # Admins/Managers/Finance can see internal notes; Employees see public only
    user_roles = [role.role_name for role in current_user.roles]
    include_internal = any(role in ("Admin", "Manager", "Finance") for role in user_roles)

    return await repo.list_by_pr_id(id, include_internal=include_internal)
