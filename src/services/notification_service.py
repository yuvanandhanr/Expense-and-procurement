import logging
from datetime import timezone, datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.platform_services import Notification, NotificationPreference, NotificationTemplate
from src.repositories.platform_services import (
    NotificationRepository,
    NotificationPreferenceRepository,
    NotificationTemplateRepository
)
from src.services.email_service import EmailService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service managing in-app alerts and notifications matching user preferences.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notification_repo = NotificationRepository(db)
        self.pref_repo = NotificationPreferenceRepository(db)
        self.template_repo = NotificationTemplateRepository(db)
        self.email_service = EmailService(db)

    async def create_template_if_not_exists(self, name: str, subject: str, body_template: str) -> NotificationTemplate:
        template = await self.template_repo.get_by_name(name)
        if not template:
            template = NotificationTemplate(
                name=name,
                subject=subject,
                body_template=body_template,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await self.template_repo.create(template)
        return template

    async def seed_templates(self) -> None:
        """
        Seeds standard system notification templates.
        """
        templates = [
            ("ApprovalRequestAlert", "Approval Request", "PR {pr_number} is pending your approval. justification: {justification}"),
            ("ApprovalCompletedAlert", "PR Status Update", "Your PR {pr_number} status is now {status}."),
            ("ContractExpiryAlert", "Contract Expiry Warning", "Contract {contract_number} with {vendor_name} expires on {expiry_date}."),
            ("BudgetAlertAlert", "Budget Ceiling Exceeded", "Budget code {budget_code} is currently at {percentage}% utilization."),
            ("InvoiceAlertAlert", "Invoice Status Update", "Invoice {invoice_number} is {status} for PO {po_number}."),
        ]
        for name, subject, body in templates:
            await self.create_template_if_not_exists(name, subject, body)

    async def get_or_create_preferences(self, user_id: int) -> NotificationPreference:
        pref = await self.pref_repo.get_by_user(user_id)
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                email_enabled=True,
                in_app_enabled=True,
                categories="all",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await self.pref_repo.create(pref)
        return pref

    async def send_notification(
        self,
        user_id: int,
        template_name: str,
        context: dict,
        category: str = "general",
        user_email: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Processes and sends notifications based on user preferences.
        """
        pref = await self.get_or_create_preferences(user_id)
        
        # Check if this category is enabled (defaulting to True if categories matches 'all' or is empty)
        category_enabled = True
        if pref.categories and pref.categories != "all":
            enabled_list = [c.strip().lower() for c in pref.categories.split(",")]
            category_enabled = category.lower() in enabled_list

        if not category_enabled:
            logger.info(f"Notification bypassed for User {user_id}: category '{category}' is disabled in preferences.")
            return None

        # Resolve subject and message text
        template = await self.template_repo.get_by_name(template_name)
        if template:
            title = template.subject.format(**context)
            message = template.body_template.format(**context)
        else:
            title = f"Alert: {template_name}"
            message = f"Alert context: {context}"

        # 1. Create In-App Notification if enabled
        notification = None
        if pref.in_app_enabled:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type="In-App",
                status="Unread",
                created_at=datetime.now(timezone.utc)
            )
            await self.notification_repo.create(notification)
            logger.info(f"Created In-App notification for user {user_id}: '{title}'")

        # 2. Queue Email if enabled
        if pref.email_enabled and user_email:
            # Map notification template to email template
            email_template_name = template_name.replace("Alert", "")
            await self.email_service.queue_email(
                recipient=user_email,
                template_name=email_template_name,
                context=context
            )
            logger.info(f"Queued email notification to {user_email} for user {user_id}")

        return notification

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification or notification.user_id != user_id:
            return False
        notification.status = "Read"
        notification.read_at = datetime.now(timezone.utc)
        await self.notification_repo.update(notification)
        return True

    async def archive_notification(self, notification_id: int, user_id: int) -> bool:
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification or notification.user_id != user_id:
            return False
        notification.status = "Archived"
        await self.notification_repo.update(notification)
        return True

    async def mark_all_as_read(self, user_id: int) -> int:
        notifications = await self.notification_repo.list_by_user(user_id, limit=1000)
        count = 0
        for n in notifications:
            if n.status == "Unread":
                n.status = "Read"
                n.read_at = datetime.now(timezone.utc)
                await self.notification_repo.update(n)
                count += 1
        return count
