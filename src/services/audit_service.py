import json
import logging
from datetime import timezone, datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.platform_services import AuditLog, ActivityLog
from src.repositories.platform_services import AuditLogRepository, ActivityLogRepository

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service managing application audit logging and user activity tracking.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit_repo = AuditLogRepository(db)
        self.activity_repo = ActivityLogRepository(db)

    async def log_action(
        self,
        action: str,
        module: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        record_id: Optional[str] = None,
        previous_value: Optional[Any] = None,
        new_value: Optional[Any] = None
    ) -> AuditLog:
        """
        Records a detailed, trackable, and unalterable security audit event.
        """
        # Serialize complex previous/new values to JSON strings
        prev_str = None
        if previous_value is not None:
            prev_str = json.dumps(previous_value) if isinstance(previous_value, (dict, list)) else str(previous_value)

        new_str = None
        if new_value is not None:
            new_str = json.dumps(new_value) if isinstance(new_value, (dict, list)) else str(new_value)

        audit = AuditLog(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            action=action,
            module=module,
            record_id=record_id,
            previous_value=prev_str,
            new_value=new_str
        )

        logger.info(f"Audit event: [{module}] User {user_email or user_id} executed action '{action}' on record '{record_id}'")
        await self.audit_repo.create(audit)
        return audit

    async def log_activity(
        self,
        user_id: int,
        activity_type: str,
        description: str,
        module: Optional[str] = None,
        record_id: Optional[str] = None
    ) -> ActivityLog:
        """
        Logs a user-facing operational activity for timeline feeds.
        """
        activity = ActivityLog(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            module=module,
            record_id=record_id
        )

        logger.info(f"Activity event: User {user_id} performed '{activity_type}' - '{description}'")
        await self.activity_repo.create(activity)
        return activity
