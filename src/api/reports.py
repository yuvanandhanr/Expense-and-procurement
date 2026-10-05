from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import PermissionChecker, get_current_user
from src.models.auth import User
from src.schemas.platform_services import ReportCreate, ReportResponse, ScheduledReportCreate, ScheduledReportResponse
from src.schemas.executive_report import ExecutiveReportFilterRequest, ExecutiveReportResponse
from src.services.report_service import ReportService
from src.services.executive_report_service import ExecutiveReportService
from src.repositories.platform_services import ReportRepository, ScheduledReportRepository

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Lists all generated reports.
    """
    repo = ReportRepository(db)
    reports = await repo.list_all()
    return reports


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Triggers generation of a new system export report.
    """
    service = ReportService(db)
    report = await service.generate_report_file(
        name=data.name,
        report_type=data.report_type,
        file_type=data.file_type,
        created_by=current_user.user_id
    )
    return report


@router.post("/schedule", response_model=ScheduledReportResponse)
async def create_scheduled_report(
    data: ScheduledReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Registers a new recurring scheduled report task.
    """
    repo = ScheduledReportRepository(db)
    from src.models.platform_services import ScheduledReport
    scheduled = ScheduledReport(
        name=data.name,
        report_type=data.report_type,
        frequency=data.frequency,
        recipients=data.recipients,
        format=data.format,
        is_active=True,
        created_by=current_user.user_id,
        created_at=datetime.utcnow() if hasattr(datetime, "utcnow") else None # fallback
    )
    # Import datetime here just in case
    from datetime import timezone, datetime
    scheduled.created_at = datetime.utcnow()
    
    await repo.create(scheduled)
    return scheduled


@router.post("/executive-expense/preview", response_model=ExecutiveReportResponse)
async def preview_executive_report(
    filters: ExecutiveReportFilterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Previews the Dataeko Executive Financial Report. Strictly CFO & Finance Admin only.
    """
    # Verify user role
    from src.models.auth import Role
    user_roles = [r.name for r in getattr(current_user, "roles", [])]
    allowed = {"Admin", "CEO", "CFO", "Finance Manager", "Finance"}
    if not (allowed.intersection(set(user_roles)) or getattr(current_user, "is_superuser", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to CFO and Finance Admin personnel."
        )

    service = ExecutiveReportService(db)
    report_data = await service.compile_executive_report(filters, current_user)
    return report_data


@router.post("/executive-expense/generate", response_model=ReportResponse)
async def generate_executive_pdf_report(
    filters: ExecutiveReportFilterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generates and saves the official Dataeko branded executive PDF report.
    """
    user_roles = [r.name for r in getattr(current_user, "roles", [])]
    allowed = {"Admin", "CEO", "CFO", "Finance Manager", "Finance"}
    if not (allowed.intersection(set(user_roles)) or getattr(current_user, "is_superuser", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to CFO and Finance Admin personnel."
        )

    service = ExecutiveReportService(db)
    report_data = await service.compile_executive_report(filters, current_user)
    file_path = await service.generate_executive_pdf_file(report_data, current_user.user_id)

    from src.models.platform_services import Report
    repo = ReportRepository(db)
    report = Report(
        name=f"Dataeko Executive Dossier ({report_data['document_metadata']['document_id']})",
        report_type="Executive Expense",
        file_type="PDF",
        file_path=file_path,
        created_by=current_user.user_id,
        status="Completed",
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    await repo.create(report)
    return report
