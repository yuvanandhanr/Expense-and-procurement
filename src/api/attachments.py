from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.models.attachment import PRAttachment
from src.schemas.attachment import PRAttachmentCreate, PRAttachmentSchema
from src.repositories.attachment import PRAttachmentRepository
from src.api.purchase_requisitions import check_pr_access

router = APIRouter(prefix="/pr", tags=["PR Attachments"])


@router.post("/{id}/attachments", response_model=PRAttachmentSchema, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    id: int,
    data: PRAttachmentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = PRAttachmentRepository(db)

    # Verify access to PR
    from src.repositories.purchase_requisition import PRRepository
    pr_repo = PRRepository(db)
    pr = await pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    check_pr_access(pr, current_user)

    # Enforce file format constraints (PDF, DOCX, PNG, JPEG)
    ext = data.file_type.lower()
    if ext not in ("pdf", "docx", "png", "jpeg", "jpg"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed formats: PDF, DOCX, PNG, JPEG"
        )

    attachment = PRAttachment(
        pr_id=id,
        file_name=data.file_name,
        file_path=data.file_path,
        file_type=data.file_type,
        file_size=data.file_size,
        uploaded_by=current_user.user_id,
        created_at=datetime.utcnow()
    )
    return await repo.create(attachment)


@router.get("/{id}/attachments", response_model=List[PRAttachmentSchema])
async def list_attachments(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = PRAttachmentRepository(db)

    # Verify access to PR
    from src.repositories.purchase_requisition import PRRepository
    pr_repo = PRRepository(db)
    pr = await pr_repo.get_by_id(id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    check_pr_access(pr, current_user)

    return await repo.list_by_pr_id(id)
