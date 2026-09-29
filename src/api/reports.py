from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import PermissionChecker, get_current_user
from src.models.auth import User
from src.schemas.platform_services import ReportCreate, ReportResponse, ScheduledReportCreate, ScheduledReportResponse
from src.services.report_service import ReportService
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
        created_at=datetime.now(timezone.utc) if hasattr(datetime, "utcnow") else None # fallback
    )
    # Import datetime here just in case
    from datetime import timezone, datetime
    scheduled.created_at = datetime.now(timezone.utc)
    
    await repo.create(scheduled)
    return scheduled
