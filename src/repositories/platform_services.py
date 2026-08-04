from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.base import BaseRepository
from src.models.platform_services import (
    NotificationTemplate,
    Notification,
    NotificationPreference,
    AuditLog,
    ActivityLog,
    Report,
    ScheduledReport,
    DashboardWidget,
    SavedFilter,
    SearchIndex,
    Attachment,
    AttachmentVersion,
    Job,
    JobHistory,
    SystemHealth,
    SystemMetric,
    SystemSetting,
    EmailTemplate,
    EmailQueue,
    CacheMetadata,
)


class NotificationTemplateRepository(BaseRepository[NotificationTemplate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(NotificationTemplate, session)

    async def get_by_id(self, entity_id: int) -> Optional[NotificationTemplate]:
        return await self.session.get(self.model, entity_id)

    async def get_by_name(self, name: str) -> Optional[NotificationTemplate]:
        query = select(self.model).where(self.model.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Notification, session)

    async def get_by_id(self, entity_id: int) -> Optional[Notification]:
        return await self.session.get(self.model, entity_id)

    async def list_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Notification]:
        query = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(NotificationPreference, session)

    async def get_by_id(self, entity_id: int) -> Optional[NotificationPreference]:
        return await self.session.get(self.model, entity_id)

    async def get_by_user(self, user_id: int) -> Optional[NotificationPreference]:
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)

    async def get_by_id(self, entity_id: int) -> Optional[AuditLog]:
        return await self.session.get(self.model, entity_id)

    async def list_logs(self, module: Optional[str] = None, action: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        query = select(self.model)
        if module:
            query = query.where(self.model.module == module)
        if action:
            query = query.where(self.model.action == action)
        query = query.order_by(self.model.timestamp.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ActivityLog, session)

    async def get_by_id(self, entity_id: int) -> Optional[ActivityLog]:
        return await self.session.get(self.model, entity_id)

    async def list_by_user(self, user_id: int, limit: int = 50) -> List[ActivityLog]:
        query = select(self.model).where(self.model.user_id == user_id).order_by(self.model.timestamp.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Report, session)

    async def get_by_id(self, entity_id: int) -> Optional[Report]:
        return await self.session.get(self.model, entity_id)


class ScheduledReportRepository(BaseRepository[ScheduledReport]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ScheduledReport, session)

    async def get_by_id(self, entity_id: int) -> Optional[ScheduledReport]:
        return await self.session.get(self.model, entity_id)

    async def list_active(self) -> List[ScheduledReport]:
        query = select(self.model).where(self.model.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class DashboardWidgetRepository(BaseRepository[DashboardWidget]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DashboardWidget, session)

    async def get_by_id(self, entity_id: int) -> Optional[DashboardWidget]:
        return await self.session.get(self.model, entity_id)

    async def list_by_role(self, role: str) -> List[DashboardWidget]:
        query = select(self.model).where(self.model.role == role, self.model.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class SavedFilterRepository(BaseRepository[SavedFilter]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SavedFilter, session)

    async def get_by_id(self, entity_id: int) -> Optional[SavedFilter]:
        return await self.session.get(self.model, entity_id)

    async def list_by_user_module(self, user_id: int, module: str) -> List[SavedFilter]:
        query = select(self.model).where(self.model.user_id == user_id, self.model.module == module)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class SearchIndexRepository(BaseRepository[SearchIndex]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SearchIndex, session)

    async def get_by_id(self, entity_id: int) -> Optional[SearchIndex]:
        return await self.session.get(self.model, entity_id)

    async def search(self, query_str: str, limit: int = 100) -> List[SearchIndex]:
        # Simple case-insensitive search on content
        query = select(self.model).where(self.model.content.ilike(f"%{query_str}%")).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class AttachmentRepository(BaseRepository[Attachment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Attachment, session)

    async def get_by_id(self, entity_id: int) -> Optional[Attachment]:
        return await self.session.get(self.model, entity_id)

    async def get_by_entity(self, entity_type: str, entity_id: str) -> List[Attachment]:
        query = select(self.model).where(self.model.entity_type == entity_type, self.model.entity_id == entity_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class AttachmentVersionRepository(BaseRepository[AttachmentVersion]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AttachmentVersion, session)

    async def get_by_id(self, entity_id: int) -> Optional[AttachmentVersion]:
        return await self.session.get(self.model, entity_id)


class JobRepository(BaseRepository[Job]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Job, session)

    async def get_by_id(self, entity_id: int) -> Optional[Job]:
        return await self.session.get(self.model, entity_id)

    async def get_by_type(self, job_type: str) -> Optional[Job]:
        query = select(self.model).where(self.model.job_type == job_type)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class JobHistoryRepository(BaseRepository[JobHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(JobHistory, session)

    async def get_by_id(self, entity_id: int) -> Optional[JobHistory]:
        return await self.session.get(self.model, entity_id)


class SystemHealthRepository(BaseRepository[SystemHealth]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SystemHealth, session)

    async def get_by_id(self, entity_id: int) -> Optional[SystemHealth]:
        return await self.session.get(self.model, entity_id)

    async def get_latest_by_component(self, component: str) -> Optional[SystemHealth]:
        query = select(self.model).where(self.model.component == component).order_by(self.model.checked_at.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class SystemMetricRepository(BaseRepository[SystemMetric]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SystemMetric, session)

    async def get_by_id(self, entity_id: int) -> Optional[SystemMetric]:
        return await self.session.get(self.model, entity_id)

    async def list_recent(self, metric_name: str, limit: int = 50) -> List[SystemMetric]:
        query = select(self.model).where(self.model.metric_name == metric_name).order_by(self.model.timestamp.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class SystemSettingRepository(BaseRepository[SystemSetting]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SystemSetting, session)

    async def get_by_id(self, entity_id: int) -> Optional[SystemSetting]:
        return await self.session.get(self.model, entity_id)

    async def get_by_key(self, key: str) -> Optional[SystemSetting]:
        query = select(self.model).where(self.model.key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class EmailTemplateRepository(BaseRepository[EmailTemplate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EmailTemplate, session)

    async def get_by_id(self, entity_id: int) -> Optional[EmailTemplate]:
        return await self.session.get(self.model, entity_id)

    async def get_by_name(self, name: str) -> Optional[EmailTemplate]:
        query = select(self.model).where(self.model.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class EmailQueueRepository(BaseRepository[EmailQueue]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EmailQueue, session)

    async def get_by_id(self, entity_id: int) -> Optional[EmailQueue]:
        return await self.session.get(self.model, entity_id)

    async def list_pending(self, limit: int = 50) -> List[EmailQueue]:
        query = select(self.model).where(self.model.status == "Pending").order_by(self.model.created_at.asc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class CacheMetadataRepository(BaseRepository[CacheMetadata]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CacheMetadata, session)

    async def get_by_id(self, entity_id: int) -> Optional[CacheMetadata]:
        return await self.session.get(self.model, entity_id)

    async def get_by_key(self, key: str) -> Optional[CacheMetadata]:
        query = select(self.model).where(self.model.key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
