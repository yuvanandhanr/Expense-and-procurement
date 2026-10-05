import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.platform_services import AttachmentResponse
from src.services.file_service import AttachmentService

router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=AttachmentResponse)
async def upload_file(
    entity_type: str = Form(..., description="Entity type: PR, PO, Vendor, Invoice, Contract, etc."),
    entity_id: str = Form(..., description="ID of the entity in the target context"),
    category: str = Form(..., description="Category: Invoices, Contracts, Vendor Documents, specs, etc."),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Uploads a file under a specified entity and category. Validates format and controls version updates.
    """
    try:
        content = await file.read()
        service = AttachmentService(db)
        attachment = await service.upload_file(
            entity_type=entity_type,
            entity_id=entity_id,
            category=category,
            filename=file.filename,
            content=content,
            uploaded_by=current_user.user_id
        )
        return attachment
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during file upload: {str(e)}"
        )


@router.get("/{attachment_id}")
async def download_file(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Downloads or previews a previously uploaded file.
    """
    service = AttachmentService(db)
    filename, file_type, content = await service.get_file_content(attachment_id)
    
    # Map file_type extension to typical headers
    media_type = "application/octet-stream"
    if file_type == ".pdf":
        media_type = "application/pdf"
    elif file_type == ".png":
        media_type = "image/png"
    elif file_type in {".jpg", ".jpeg"}:
        media_type = "image/jpeg"
    elif file_type == ".csv":
        media_type = "text/csv"
    elif file_type == ".xlsx":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/download/{file_id}")
async def download_file_alias(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Alias route supporting both attachments and report downloads.
    """
    import os
    from src.repositories.platform_services import ReportRepository
    from src.schemas.executive_report import ExecutiveReportFilterRequest
    from src.services.executive_report_service import ExecutiveReportService

    # 1. Try Report first
    repo = ReportRepository(db)
    report = await repo.get_by_id(file_id)
    if report:
        if report.file_path and os.path.exists(report.file_path):
            with open(report.file_path, "rb") as f:
                content = f.read()
            filename = os.path.basename(report.file_path)
        else:
            service = ExecutiveReportService(db)
            data = await service.compile_executive_report(ExecutiveReportFilterRequest(), current_user)
            path = await service.generate_executive_pdf_file(data, current_user.user_id)
            with open(path, "rb") as f:
                content = f.read()
            filename = f"Dataeko_Report_{file_id}.pdf"

        media_type = "application/pdf" if getattr(report, "file_type", "PDF") == "PDF" else "application/octet-stream"
        return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    # 2. Try Attachment
    try:
        service = AttachmentService(db)
        filename, file_type, content = await service.get_file_content(file_id)
        media_type = "application/pdf" if file_type == ".pdf" else "application/octet-stream"
        return Response(content=content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    except Exception:
        raise HTTPException(status_code=404, detail="Requested file not found")

