import os
import csv
import io
import logging
from datetime import timezone, datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook
from src.models.purchase_requisition import PurchaseRequisition
from src.models.purchase_order import PurchaseOrder
from src.models.vendor import Vendor
from src.models.platform_services import Report, ScheduledReport
from src.repositories.platform_services import ReportRepository, ScheduledReportRepository
from src.services.email_service import EmailService

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service generating custom CSV/Excel/PDF export sheets and executing scheduled deliveries.
    """

    def __init__(self, db: AsyncSession, report_dir: str = "reports") -> None:
        self.db = db
        self.report_repo = ReportRepository(db)
        self.sched_repo = ScheduledReportRepository(db)
        self.email_service = EmailService(db)
        self.report_dir = report_dir
        os.makedirs(self.report_dir, exist_ok=True)

    async def get_report_data(self, report_type: str) -> Tuple[List[str], List[List[Any]]]:
        """
        Gathers raw data for the specified report type.
        """
        report_type_upper = report_type.upper()
        headers = []
        rows = []

        if report_type_upper == "PR":
            headers = ["PR ID", "PR Number", "Title", "Requestor ID", "Total Estimated", "Status", "Created At"]
            query = select(PurchaseRequisition).order_by(PurchaseRequisition.created_at.desc())
            result = await self.db.execute(query)
            for pr in result.scalars().all():
                rows.append([
                    pr.pr_id,
                    pr.pr_number,
                    pr.title,
                    pr.requestor_id,
                    float(pr.total_estimated_amount),
                    pr.status,
                    pr.created_at.isoformat() if pr.created_at else ""
                ])

        elif report_type_upper == "PO":
            headers = ["PO ID", "PO Number", "Vendor ID", "Total Amount", "Status", "Created At"]
            query = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
            result = await self.db.execute(query)
            for po in result.scalars().all():
                rows.append([
                    po.po_id,
                    po.po_number,
                    po.vendor_id,
                    float(po.total_amount),
                    po.status,
                    po.created_at.isoformat() if po.created_at else ""
                ])

        elif report_type_upper == "VENDOR":
            headers = ["Vendor ID", "Vendor Code", "Name", "Email", "Status"]
            query = select(Vendor).order_by(Vendor.name)
            result = await self.db.execute(query)
            for v in result.scalars().all():
                rows.append([
                    v.vendor_id,
                    v.code,
                    v.name,
                    v.email,
                    v.status
                ])

        else:
            # General fallback data if not specific
            headers = ["Report Name", "Generated At", "Status"]
            rows = [[report_type, datetime.utcnow().isoformat(), "Active"]]

        return headers, rows

    async def generate_report_file(self, name: str, report_type: str, file_type: str, created_by: int) -> Report:
        """
        Generates report bytes, saves the physical file, and creates a database record.
        """
        report = Report(
            name=name,
            report_type=report_type,
            file_type=file_type,
            created_by=created_by,
            status="Processing",
            created_at=datetime.utcnow()
        )
        await self.report_repo.create(report)

        try:
            headers, rows = await self.get_report_data(report_type)
            file_type_upper = file_type.upper()
            filename = f"report_{report.report_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{file_type.lower()}"
            file_path = os.path.join(self.report_dir, filename)

            if file_type_upper == "CSV":
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)

            elif file_type_upper == "EXCEL":
                wb = Workbook()
                ws = wb.active
                ws.title = report_type[:30]
                ws.append(headers)
                for r in rows:
                    ws.append(r)
                wb.save(file_path)

            elif file_type_upper == "PDF":
                # Generate a clean text-based PDF layout for mock execution
                # We can write a formatted report header and data table into a text/pdf layout
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"--- ENTERPRISE PLATFORM REPORT: {name} ---\n")
                    f.write(f"Report Type: {report_type} | Generated At: {datetime.utcnow().isoformat()}\n")
                    f.write("=" * 80 + "\n")
                    f.write("\t".join(headers) + "\n")
                    f.write("-" * 80 + "\n")
                    for r in rows:
                        f.write("\t".join(str(val) for val in r) + "\n")
                    f.write("=" * 80 + "\n")

            else:
                raise ValueError(f"Unsupported report format: {file_type}")

            report.file_path = file_path
            report.status = "Completed"
            report.completed_at = datetime.utcnow()
            await self.report_repo.update(report)
            logger.info(f"Report ID {report.report_id} generated successfully at '{file_path}'")

        except Exception as e:
            logger.error(f"Failed to generate report ID {report.report_id}: {e}", exc_info=True)
            report.status = "Failed"
            await self.report_repo.update(report)
            raise e

        return report

    async def execute_scheduled_reports(self) -> int:
        """
        Worker task pulling active schedules, compiling documents, and queuing emails.
        """
        schedules = await self.sched_repo.list_active()
        count = 0

        for sched in schedules:
            # Check if it is time to run based on frequency
            # (In a real system, we compare next_run. For mock, we execute if next_run is None or past)
            if sched.next_run and sched.next_run > datetime.utcnow():
                continue

            logger.info(f"Running scheduled report: '{sched.name}' Frequency: '{sched.frequency}'")
            try:
                report = await self.generate_report_file(
                    name=sched.name,
                    report_type=sched.report_type,
                    file_type=sched.format,
                    created_by=sched.created_by
                )

                # Queue email to recipients with report metadata
                recipients_list = [email.strip() for email in sched.recipients.split(",") if email.strip()]
                for email in recipients_list:
                    await self.email_service.queue_email(
                        recipient=email,
                        template_name="Welcome", # or standard notification template
                        context={
                            "name": "Subscriber",
                            "code": f"Report Link: {report.file_path}"
                        }
                    )

                # Update schedule run timestamps
                sched.last_run = datetime.utcnow()
                # Update next run timestamp based on frequency
                delta = timedelta(days=1)
                if sched.frequency.upper() == "WEEKLY":
                    delta = timedelta(weeks=1)
                elif sched.frequency.upper() == "MONTHLY":
                    delta = timedelta(days=30)
                sched.next_run = datetime.utcnow() + delta

                await self.sched_repo.update(sched)
                count += 1
            except Exception as e:
                logger.error(f"Scheduled report '{sched.name}' execution failed: {e}")

        return count
