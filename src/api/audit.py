from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import RoleChecker
from src.schemas.platform_services import AuditLogResponse
from src.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=List[AuditLogResponse])
async def get_audit_logs(
    module: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user = Depends(RoleChecker(["CEO", "CFO", "Finance"]))
):
    """
    Retrieves system security audit logs, filterable by module and action.
    Restricted to CEO, CFO, and Finance.
    """
    service = AuditService(db)
    logs = await service.audit_repo.list_logs(module=module, action=action, skip=skip, limit=limit)
    return logs
