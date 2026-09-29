import logging
from datetime import timezone, datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.platform_services import SystemSetting
from src.repositories.platform_services import SystemSettingRepository

logger = logging.getLogger(__name__)


class SettingService:
    """
    Service managing tenant-wide configurations and policies.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.setting_repo = SystemSettingRepository(db)

    async def get_setting_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        setting = await self.setting_repo.get_by_key(key)
        if setting:
            return setting.value
        return default

    async def update_setting(self, key: str, value: str, description: Optional[str] = None, category: str = "General") -> SystemSetting:
        setting = await self.setting_repo.get_by_key(key)
        if setting:
            setting.value = value
            if description is not None:
                setting.description = description
            setting.updated_at = datetime.utcnow()
            await self.setting_repo.update(setting)
            logger.info(f"Updated system setting: '{key}' = '{value}'")
        else:
            setting = SystemSetting(
                key=key,
                value=value,
                description=description,
                category=category,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await self.setting_repo.create(setting)
            logger.info(f"Created system setting: '{key}' = '{value}'")
        return setting

    async def list_settings(self, category: Optional[str] = None) -> List[SystemSetting]:
        query = select(SystemSetting)
        if category:
            query = query.where(SystemSetting.category == category)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def seed_default_settings(self) -> None:
        """
        Seeds standard system configurations out-of-the-box.
        """
        defaults = [
            ("org_name", "Enterprise Corp", "Name of the organization", "Organization"),
            ("org_currency", "USD", "Base currency for reporting", "Organization"),
            ("smtp_host", "smtp.mailtrap.io", "SMTP Host", "Email"),
            ("smtp_port", "2525", "SMTP Port", "Email"),
            ("upload_max_size_bytes", "10485760", "Max file size (10MB)", "Upload Limits"),
            ("password_policy_min_length", "8", "Minimum password length", "Password Policies"),
            ("session_timeout_minutes", "60", "Session timeout in minutes", "Password Policies"),
            ("retention_audit_logs_days", "365", "Audit logs retention", "Retention Policies"),
        ]

        for key, val, desc, cat in defaults:
            existing = await self.setting_repo.get_by_key(key)
            if not existing:
                await self.update_setting(key, val, desc, cat)
