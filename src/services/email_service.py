import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import timezone, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.models.platform_services import EmailQueue, EmailTemplate
from src.repositories.platform_services import EmailQueueRepository, EmailTemplateRepository

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service managing template-based emails and asynchronous queuing.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.queue_repo = EmailQueueRepository(db)
        self.template_repo = EmailTemplateRepository(db)

    async def create_template_if_not_exists(self, name: str, subject: str, body_template: str) -> EmailTemplate:
        template = await self.template_repo.get_by_name(name)
        if not template:
            template = EmailTemplate(
                name=name,
                subject=subject,
                body_template=body_template,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await self.template_repo.create(template)
        return template

    async def seed_templates(self) -> None:
        """
        Seeds standard template definitions.
        """
        templates = [
            ("Welcome", "Welcome to the Enterprise Expense Platform", "Hello {name},\n\nWelcome! Your employee account ({code}) has been created successfully."),
            ("PasswordReset", "Password Reset Request", "Hello,\n\nPlease reset your password using the following link: {link}"),
            ("ApprovalRequest", "Approval Action Required: {pr_number}", "Hello {approver_name},\n\nA purchase request ({pr_number}) for {amount} {currency} is awaiting your approval. Justification: {justification}"),
            ("ApprovalCompleted", "Approval Request Approved: {pr_number}", "Hello {requestor_name},\n\nYour purchase request ({pr_number}) has been fully approved! Status: {status}"),
            ("PurchaseOrderIssued", "Purchase Order Issued: {po_number}", "Dear {vendor_name},\n\nWe have issued Purchase Order {po_number} for {amount}. Please find the details attached."),
            ("InvoiceApproved", "Invoice Approved for Payment: {invoice_number}", "Hello,\n\nInvoice {invoice_number} has been approved for payment matching PO {po_number}."),
            ("ContractExpiry", "Contract Expiring Soon: {contract_number}", "Hello,\n\nContract {contract_number} with {vendor_name} is expiring on {expiry_date}."),
            ("RenewalReminder", "Subscription Renewal Reminder: {contract_number}", "Hello,\n\nSubscription {contract_number} is scheduled for renewal on {renewal_date}."),
            ("BudgetAlert", "CRITICAL Alert: Budget Limit Exceeded for {dept_name}", "Hello Manager,\n\nDepartment {dept_name} has consumed {percentage}% of its allocated budget for the budget code {budget_code}."),
        ]
        for name, subject, body in templates:
            await self.create_template_if_not_exists(name, subject, body)

    async def queue_email(self, recipient: str, template_name: str, context: dict) -> EmailQueue:
        """
        Renders a template and places the email into the queue.
        """
        template = await self.template_repo.get_by_name(template_name)
        if not template:
            # Fallback if templates are not seeded
            subject = f"Platform Notification: {template_name}"
            body = f"Context details: {context}"
        else:
            subject = template.subject.format(**context)
            body = template.body_template.format(**context)

        email = EmailQueue(
            recipient=recipient,
            subject=subject,
            body=body,
            status="Pending",
            retry_count=0,
            created_at=datetime.utcnow()
        )
        await self.queue_repo.create(email)
        return email

    async def send_email_immediately(self, email: EmailQueue) -> bool:
        """
        Attempts to connect via SMTP and send the email, updating status in queue.
        """
        logger.info(f"Attempting to send email to {email.recipient} via SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        try:
            # Mock or Console logging fallback if SMTP host points to mock placeholder
            if "mock" in settings.SMTP_HOST or "placeholder" in settings.SMTP_HOST or not settings.SMTP_HOST:
                logger.info(f"[SMTP CONSOLE MOCK] Email sent successfully to {email.recipient}.\nSubject: {email.subject}\nBody:\n{email.body}")
                email.status = "Sent"
                email.sent_at = datetime.utcnow()
                await self.queue_repo.update(email)
                return True

            # Real SMTP sending code
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = email.recipient
            msg["Subject"] = email.subject
            msg.attach(MIMEText(email.body, "plain"))

            # Run in a blocking threadpool if called from async, but for simplicity we run directly
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD and "mock" not in settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            email.status = "Sent"
            email.sent_at = datetime.utcnow()
            await self.queue_repo.update(email)
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {email.recipient}: {e}", exc_info=True)
            email.retry_count += 1
            email.error_message = str(e)
            if email.retry_count >= 3:
                email.status = "Failed"
            else:
                email.status = "Pending"
            await self.queue_repo.update(email)
            return False

    async def process_email_queue(self, limit: int = 20) -> int:
        """
        Pulls pending emails and tries to send them. Returns count of successfully sent emails.
        """
        pending = await self.queue_repo.list_pending(limit=limit)
        sent_count = 0
        for email in pending:
            success = await self.send_email_immediately(email)
            if success:
                sent_count += 1
        return sent_count
