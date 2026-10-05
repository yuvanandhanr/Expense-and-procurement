import json
import logging
from datetime import timezone, datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.cache.factory import get_cache
from src.models.purchase_requisition import PurchaseRequisition
from src.models.purchase_order import PurchaseOrder
from src.models.vendor import Vendor, VendorPerformance
from src.models.contract import Contract
from src.models.assets import Asset
from src.models.invoice import VendorInvoice
from src.models.expense import ExpenseReport
from src.models.rfq import RequestForQuotation
from src.models.payments import PaymentRequest
from src.models.organization import Department, BudgetCode
from src.models.platform_services import ActivityLog, DashboardWidget

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service generating data models for Executive Dashboards and Analytics modules.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.cache = get_cache()

    async def get_dashboard_data(self, role: str, user_id: int) -> Dict[str, Any]:
        """
        Compiles executive dashboard data filtered by role and caches it.
        """
        # Base dashboard widgets - computed live in real-time
        data = {
            "role": role,
            "timestamp": datetime.utcnow().isoformat(),
            "widgets": {}
        }

        # 1. Recent Activities widget (Common to all roles)
        data["widgets"]["recent_activities"] = await self._get_recent_activities()

        # Compile specific metrics based on role
        role_upper = role.upper()

        # Differentiated Monthly (MTD) and Yearly (YTD) Spending Metrics
        spend_summary = await self._get_monthly_and_yearly_spend_summary(user_id=user_id if role_upper == "EMPLOYEE" else None)
        data["widgets"]["financial_cadence"] = spend_summary

        if role_upper in ("CEO", "CFO", "FINANCE", "FINANCE MANAGER", "ADMIN"):
            data["widgets"]["pending_approvals"] = await self._get_pending_approvals_count()
            data["widgets"]["department_spend"] = await self._get_department_spend()
            data["widgets"]["department_monthly_spend"] = await self._get_department_spend(period="month")
            data["widgets"]["department_yearly_spend"] = await self._get_department_spend(period="year")
            data["widgets"]["budget_utilization"] = await self._get_budget_utilization()
            data["widgets"]["employee_reimbursements"] = await self._get_reimbursements_summary()
            data["widgets"]["vendor_invoices"] = await self._get_vendor_invoices_summary()
            data["widgets"]["payment_status"] = await self._get_payment_status_counts()
            data["widgets"]["top_vendors"] = await self._get_top_vendors()

        if role_upper in ("CFO", "FINANCE MANAGER", "PROCUREMENT", "ADMIN"):
            data["widgets"]["purchase_orders"] = await self._get_po_summary()
            data["widgets"]["vendor_performance"] = await self._get_vendor_performance_summary()
            data["widgets"]["monthly_procurement"] = await self._get_monthly_procurement_trends()
            data["widgets"]["contract_expiry"] = await self._get_expiring_contracts_count()
            data["widgets"]["open_requests"] = await self._get_open_procurement_requests()
            data["widgets"]["procurement_metrics"] = await self._get_procurement_metrics()

        if role_upper in ("IT", "FINANCE", "FINANCE MANAGER", "ADMIN"):
            data["widgets"]["asset_summary"] = await self._get_asset_summary()
            data["widgets"]["low_stock_alerts"] = await self._get_low_stock_alerts()
            data["widgets"]["amc_expiry"] = await self._get_expiring_amc_count()

        if role_upper == "MANAGER":
            data["widgets"]["pending_approvals"] = await self._get_pending_approvals_count(manager_id=user_id)
            data["widgets"]["department_spend"] = await self._get_department_spend(manager_id=user_id)
            data["widgets"]["department_monthly_spend"] = await self._get_department_spend(manager_id=user_id, period="month")
            data["widgets"]["department_yearly_spend"] = await self._get_department_spend(manager_id=user_id, period="year")
            data["widgets"]["employee_reimbursements"] = await self._get_reimbursements_summary()
            data["widgets"]["vendor_invoices"] = await self._get_vendor_invoices_summary()

        # Personal metrics for all roles ("My Requests")
        data["widgets"]["my_purchase_requests"] = await self._get_employee_pr_summary(user_id)
        data["widgets"]["my_reimbursements"] = await self._get_reimbursements_summary(employee_id=user_id)
        data["widgets"]["my_monthly_trend"] = await self._get_employee_monthly_trend(employee_id=user_id)
        data["widgets"]["my_requisitions"] = await self._get_employee_my_requisitions(user_id)
        data["widgets"]["my_assets"] = await self._get_employee_my_assets(user_id)
        data["widgets"]["recent_expenses"] = await self._get_employee_recent_expenses(user_id)

        # Real-time metrics computed directly
        return data

    async def get_spend_analytics(self, timeframe: str = "all") -> Dict[str, Any]:
        """
        Gathers spending trends across departments, vendors, categories, months, and fiscal years.
        """
        data = {
            "timeframe": timeframe,
            "financial_cadence": await self._get_monthly_and_yearly_spend_summary(),
            "department_spend": await self._get_department_spend(),
            "department_monthly_spend": await self._get_department_spend(period="month"),
            "department_yearly_spend": await self._get_department_spend(period="year"),
            "vendor_spend": await self._get_top_vendors(),
            "category_spend": await self._get_category_spend(),
            "monthly_trends": await self._get_monthly_procurement_trends(),
            "yearly_trends": await self._get_yearly_trends(),
            "budget_consumption": await self._get_budget_utilization(),
        }
        return data

    async def get_vendor_analytics(self) -> List[Dict[str, Any]]:
        """
        Aggregates metrics representing vendor spend and quality ratings.
        """
        query = select(
            Vendor.vendor_id,
            Vendor.vendor_name,
            Vendor.vendor_code,
            func.coalesce(func.avg(VendorPerformance.quality_score), 0).label("avg_quality"),
            func.coalesce(func.avg(VendorPerformance.delivery_performance), 0).label("avg_delivery"),
            func.coalesce(func.avg(VendorPerformance.contract_compliance), 0).label("avg_compliance")
        ).outerjoin(
            VendorPerformance, Vendor.vendor_id == VendorPerformance.vendor_id
        ).group_by(Vendor.vendor_id, Vendor.vendor_name, Vendor.vendor_code)

        result = await self.db.execute(query)
        vendors = []
        for row in result.all():
            vendors.append({
                "vendor_id": row.vendor_id,
                "name": row.vendor_name,
                "code": row.vendor_code,
                "quality_rating": float(row.avg_quality),
                "delivery_rating": float(row.avg_delivery),
                "compliance_rating": float(row.avg_compliance),
            })
        return vendors

    async def get_budget_analytics(self) -> List[Dict[str, Any]]:
        return await self._get_budget_utilization()

    # --- Private Widget Query Implementation Helpers ---

    async def _get_recent_activities(self) -> List[Dict[str, Any]]:
        query = select(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(10)
        result = await self.db.execute(query)
        activities = []
        for act in result.scalars().all():
            activities.append({
                "timestamp": act.timestamp.isoformat(),
                "user_id": act.user_id,
                "activity_type": act.activity_type,
                "description": act.description,
                "module": act.module
            })
        return activities

    async def _get_pending_approvals_count(self, manager_id: Optional[int] = None) -> int:
        from src.models.expense import ExpenseApproval
        from src.models.approval import ApprovalStep
        from src.models.auth import User
        count = 0
        if manager_id:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            result = await self.db.execute(select(User).options(selectinload(User.roles)).where(User.user_id == manager_id))
            user = result.scalar_one_or_none()
            if user:
                user_roles = [r.role_id for r in user.roles]
                
                # PR approvals
                pr_query = select(func.count(ApprovalStep.step_id)).where(
                    (ApprovalStep.approver_id == manager_id) |
                    (ApprovalStep.approver_id.is_(None) & ApprovalStep.approver_role_id.in_(user_roles)),
                    ApprovalStep.status == "Pending"
                )
                pr_res = await self.db.execute(pr_query)
                count += pr_res.scalar() or 0
                
                # Expense approvals
                exp_query = select(func.count(ExpenseApproval.approval_id)).where(
                    ExpenseApproval.approver_id == manager_id,
                    ExpenseApproval.status == "Pending"
                )
                exp_res = await self.db.execute(exp_query)
                count += exp_res.scalar() or 0
        return count

    async def _get_monthly_and_yearly_spend_summary(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates Month-to-Date (MTD) and Year-to-Date (YTD) spending across expenses, POs, and vendor invoices.
        """
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        start_of_year = datetime(now.year, 1, 1)
        
        # Calculate start of prior month
        if now.month == 1:
            start_of_prior_month = datetime(now.year - 1, 12, 1)
            end_of_prior_month = datetime(now.year - 1, 12, 31, 23, 59, 59)
        else:
            start_of_prior_month = datetime(now.year, now.month - 1, 1)
            end_of_prior_month = start_of_month - timedelta(seconds=1)

        # 1. Expense Reports
        exp_mtd_q = select(func.coalesce(func.sum(ExpenseReport.total_amount), 0), func.count(ExpenseReport.expense_report_id)).where(
            ExpenseReport.status.in_(["Approved", "Finance Verified", "Paid", "Approved for Payment", "Payment Requested"]),
            ExpenseReport.created_at >= start_of_month
        )
        exp_ytd_q = select(func.coalesce(func.sum(ExpenseReport.total_amount), 0), func.count(ExpenseReport.expense_report_id)).where(
            ExpenseReport.status.in_(["Approved", "Finance Verified", "Paid", "Approved for Payment", "Payment Requested"]),
            ExpenseReport.created_at >= start_of_year
        )
        exp_prior_q = select(func.coalesce(func.sum(ExpenseReport.total_amount), 0)).where(
            ExpenseReport.status.in_(["Approved", "Finance Verified", "Paid", "Approved for Payment", "Payment Requested"]),
            ExpenseReport.created_at >= start_of_prior_month,
            ExpenseReport.created_at <= end_of_prior_month
        )

        if user_id:
            exp_mtd_q = exp_mtd_q.where(ExpenseReport.employee_id == user_id)
            exp_ytd_q = exp_ytd_q.where(ExpenseReport.employee_id == user_id)
            exp_prior_q = exp_prior_q.where(ExpenseReport.employee_id == user_id)

        exp_mtd_res = (await self.db.execute(exp_mtd_q)).first()
        exp_ytd_res = (await self.db.execute(exp_ytd_q)).first()
        exp_prior_res = (await self.db.execute(exp_prior_q)).scalar() or 0.0

        # 2. Purchase Orders (Procurement Spend)
        po_mtd_q = select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0), func.count(PurchaseOrder.po_id)).where(
            PurchaseOrder.status.in_(["Issued", "Delivered", "Billed", "Accepted", "Completed"]),
            PurchaseOrder.created_at >= start_of_month
        )
        po_ytd_q = select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0), func.count(PurchaseOrder.po_id)).where(
            PurchaseOrder.status.in_(["Issued", "Delivered", "Billed", "Accepted", "Completed"]),
            PurchaseOrder.created_at >= start_of_year
        )
        po_prior_q = select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0)).where(
            PurchaseOrder.status.in_(["Issued", "Delivered", "Billed", "Accepted", "Completed"]),
            PurchaseOrder.created_at >= start_of_prior_month,
            PurchaseOrder.created_at <= end_of_prior_month
        )

        po_mtd_res = (await self.db.execute(po_mtd_q)).first()
        po_ytd_res = (await self.db.execute(po_ytd_q)).first()
        po_prior_res = (await self.db.execute(po_prior_q)).scalar() or 0.0

        exp_mtd_amt = float(exp_mtd_res[0] or 0.0) if exp_mtd_res else 0.0
        exp_ytd_amt = float(exp_ytd_res[0] or 0.0) if exp_ytd_res else 0.0
        po_mtd_amt = float(po_mtd_res[0] or 0.0) if po_mtd_res else 0.0
        po_ytd_amt = float(po_ytd_res[0] or 0.0) if po_ytd_res else 0.0

        total_mtd = exp_mtd_amt + po_mtd_amt
        total_ytd = exp_ytd_amt + po_ytd_amt
        total_prior = float(exp_prior_res) + float(po_prior_res)

        mom_growth = ((total_mtd - total_prior) / total_prior * 100) if total_prior > 0 else 0.0

        return {
            "current_month_name": now.strftime("%B %Y"),
            "current_fiscal_year": f"FY {now.year}",
            "monthly_spend": round(total_mtd, 2),
            "yearly_spend": round(total_ytd, 2),
            "prior_month_spend": round(total_prior, 2),
            "mom_growth_percent": round(mom_growth, 1),
            "reimbursements": {
                "monthly_amount": round(exp_mtd_amt, 2),
                "monthly_count": exp_mtd_res[1] if exp_mtd_res else 0,
                "yearly_amount": round(exp_ytd_amt, 2),
                "yearly_count": exp_ytd_res[1] if exp_ytd_res else 0,
            },
            "procurement": {
                "monthly_amount": round(po_mtd_amt, 2),
                "monthly_count": po_mtd_res[1] if po_mtd_res else 0,
                "yearly_amount": round(po_ytd_amt, 2),
                "yearly_count": po_ytd_res[1] if po_ytd_res else 0,
            }
        }

    async def _get_low_stock_alerts(self) -> Dict[str, Any]:
        """
        Audits asset inventory and returns items where available stock is <= 5.
        """
        from src.models.assets import AssetCategory
        query = select(
            AssetCategory.category_name,
            func.count(Asset.asset_id).label("available_count")
        ).join(
            Asset, AssetCategory.category_id == Asset.category_id
        ).where(
            Asset.status.in_(["Available", "Unassigned", "In Stock"])
        ).group_by(AssetCategory.category_name)

        result = await self.db.execute(query)
        low_stock_categories = []
        total_low_stock_count = 0

        for row in result.all():
            count = int(row.available_count or 0)
            if count <= 5:
                low_stock_categories.append({
                    "category": row.category_name,
                    "available_stock": count,
                    "threshold": 5,
                    "action_required": "Push to Finance Manager / RFQ"
                })
                total_low_stock_count += 1

        return {
            "has_low_stock": len(low_stock_categories) > 0,
            "low_stock_count": total_low_stock_count,
            "items": low_stock_categories
        }

    async def _get_department_spend(self, manager_id: Optional[int] = None, period: Optional[str] = None) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        query = select(
            Department.department_name,
            func.sum(PurchaseRequisition.total_estimated_amount).label("total_spend")
        ).join(
            PurchaseRequisition, Department.department_id == PurchaseRequisition.department_id
        ).where(
            PurchaseRequisition.status.in_(["Approved", "Closed"])
        )

        if period == "month":
            start_of_month = datetime(now.year, now.month, 1)
            query = query.where(PurchaseRequisition.created_at >= start_of_month)
        elif period == "year":
            start_of_year = datetime(now.year, 1, 1)
            query = query.where(PurchaseRequisition.created_at >= start_of_year)

        query = query.group_by(Department.department_name)
        
        result = await self.db.execute(query)
        spend = []
        for row in result.all():
            spend.append({
                "department": row.department_name,
                "spend": float(row.total_spend or 0.0)
            })
        return spend

    async def _get_budget_utilization(self) -> List[Dict[str, Any]]:
        # Map budget code and utilization metrics
        query = select(
            BudgetCode.budget_code,
            BudgetCode.description,
            BudgetCode.annual_budget,
            BudgetCode.available_budget
        )
        result = await self.db.execute(query)
        budgets = []
        for row in result.all():
            allocated = float(row.annual_budget or 0.0)
            available = float(row.available_budget or 0.0)
            utilized = allocated - available
            percentage = (utilized / allocated * 100) if allocated > 0 else 0.0
            budgets.append({
                "budget_code": row.budget_code,
                "name": row.description,
                "allocated": allocated,
                "utilized": utilized,
                "available": available,
                "percentage": percentage
            })
        return budgets

    async def _get_reimbursements_summary(self, employee_id: Optional[int] = None) -> Dict[str, Any]:
        query = select(
            func.count(VendorInvoice.invoice_id),
            func.sum(VendorInvoice.grand_total)
        ).where(VendorInvoice.employee_id.isnot(None))
        
        if employee_id:
            query = query.where(VendorInvoice.employee_id == employee_id)
            
        result = await self.db.execute(query)
        row = result.first()
        return {
            "count": row[0] or 0,
            "amount": float(row[1] or 0.0)
        }

    async def _get_vendor_invoices_summary(self) -> Dict[str, Any]:
        query = select(
            func.count(VendorInvoice.invoice_id),
            func.sum(VendorInvoice.grand_total)
        ).where(VendorInvoice.employee_id.is_(None))
        
        result = await self.db.execute(query)
        row = result.first()
        return {
            "count": row[0] or 0,
            "amount": float(row[1] or 0.0)
        }
        
    async def _get_employee_monthly_trend(self, employee_id: int) -> List[Dict[str, Any]]:
        query = select(
            func.to_char(VendorInvoice.invoice_date, 'YYYY-MM').label("month"),
            func.sum(VendorInvoice.grand_total).label("total_spend")
        ).where(
            VendorInvoice.employee_id == employee_id,
            VendorInvoice.status.in_(["Approved", "Paid"])
        ).group_by("month").order_by("month")
        try:
            result = await self.db.execute(query)
            return [{"month": row.month, "spend": float(row.total_spend or 0.0)} for row in result.all()]
        except Exception:
            return []

    async def _get_payment_status_counts(self) -> Dict[str, int]:
        query = select(
            PaymentRequest.status,
            func.count(PaymentRequest.payment_request_id)
        ).group_by(PaymentRequest.status)
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def _get_top_vendors(self) -> List[Dict[str, Any]]:
        query = select(
            Vendor.vendor_name,
            func.sum(PurchaseOrder.total_amount).label("total_po_spend")
        ).join(
            PurchaseOrder, Vendor.vendor_id == PurchaseOrder.vendor_id
        ).where(
            PurchaseOrder.status.in_(["Issued", "Delivered", "Billed"])
        ).group_by(Vendor.vendor_name).order_by(desc("total_po_spend")).limit(5)
        
        result = await self.db.execute(query)
        vendors = []
        for row in result.all():
            vendors.append({
                "vendor": row.vendor_name,
                "spend": float(row.total_po_spend or 0.0)
            })
        return vendors

    async def _get_po_summary(self) -> Dict[str, Any]:
        query = select(
            PurchaseOrder.status,
            func.count(PurchaseOrder.po_id),
            func.sum(PurchaseOrder.total_amount)
        ).group_by(PurchaseOrder.status)
        result = await self.db.execute(query)
        summary = {"counts": {}, "amounts": {}}
        for row in result.all():
            summary["counts"][row[0]] = row[1]
            summary["amounts"][row[0]] = float(row[2] or 0.0)
        return summary

    async def _get_vendor_performance_summary(self) -> List[Dict[str, Any]]:
        query = select(
            Vendor.vendor_name,
            func.avg(VendorPerformance.rating).label("avg_score")
        ).join(
            VendorPerformance, Vendor.vendor_id == VendorPerformance.vendor_id
        ).group_by(Vendor.vendor_name).order_by(desc("avg_score")).limit(5)
        result = await self.db.execute(query)
        return [{"vendor": row[0], "score": float(row[1] or 0.0)} for row in result.all()]

    async def _get_monthly_procurement_trends(self) -> List[Dict[str, Any]]:
        # Group spend by year/month string
        query = select(
            func.to_char(PurchaseOrder.created_at, 'YYYY-MM').label("month"),
            func.sum(PurchaseOrder.total_amount).label("total_spend")
        ).where(
            PurchaseOrder.status.in_(["Issued", "Delivered", "Billed"])
        ).group_by("month").order_by("month")
        try:
            result = await self.db.execute(query)
            return [{"month": row.month, "spend": float(row.total_spend or 0.0)} for row in result.all()]
        except Exception:
            # Fallback for SQL engines where to_char is not supported (e.g. SQLite tests)
            return []

    async def _get_yearly_trends(self) -> List[Dict[str, Any]]:
        query = select(
            func.to_char(PurchaseOrder.created_at, 'YYYY').label("year"),
            func.sum(PurchaseOrder.total_amount).label("total_spend")
        ).group_by("year").order_by("year")
        try:
            result = await self.db.execute(query)
            return [{"year": row.year, "spend": float(row.total_spend or 0.0)} for row in result.all()]
        except Exception:
            return []

    async def _get_expiring_contracts_count(self) -> int:
        thirty_days_later = datetime.utcnow() + timedelta(days=30)
        query = select(func.count(Contract.contract_id)).where(
            Contract.end_date <= thirty_days_later,
            Contract.status == "Active"
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_open_procurement_requests(self) -> int:
        query = select(func.count(PurchaseRequisition.pr_id)).where(
            PurchaseRequisition.status.in_(["Pending Approval", "Approved"])
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
        
    async def _get_procurement_metrics(self) -> Dict[str, int]:
        vendors_query = select(func.count(Vendor.vendor_id)).where(Vendor.status == "Active")
        rfqs_query = select(func.count(RequestForQuotation.rfq_id)).where(RequestForQuotation.status == "Open")
        pos_query = select(func.count(PurchaseOrder.po_id)).where(PurchaseOrder.status.in_(["Issued", "Processing", "Delivered", "Billed"]))
        contracts_query = select(func.count(Contract.contract_id)).where(Contract.status == "Active")
        
        vendors_count = (await self.db.execute(vendors_query)).scalar() or 0
        rfqs_count = (await self.db.execute(rfqs_query)).scalar() or 0
        pos_count = (await self.db.execute(pos_query)).scalar() or 0
        contracts_count = (await self.db.execute(contracts_query)).scalar() or 0
        
        return {
            "active_vendors": vendors_count,
            "pending_rfqs": rfqs_count,
            "open_pos": pos_count,
            "active_contracts": contracts_count
        }

    async def _get_asset_summary(self) -> Dict[str, int]:
        query = select(
            Asset.status,
            func.count(Asset.asset_id)
        ).group_by(Asset.status)
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def _get_expiring_amc_count(self) -> int:
        thirty_days_later = datetime.utcnow() + timedelta(days=30)
        query = select(func.count(Contract.contract_id)).where(
            Contract.contract_type == "AMC",
            Contract.end_date <= thirty_days_later,
            Contract.status == "Active"
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_employee_pr_summary(self, user_id: int) -> Dict[str, int]:
        query = select(
            PurchaseRequisition.status,
            func.count(PurchaseRequisition.pr_id)
        ).where(
            PurchaseRequisition.requestor_id == user_id
        ).group_by(PurchaseRequisition.status)
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def _get_employee_my_requisitions(self, user_id: int) -> List[Dict[str, Any]]:
        query = select(PurchaseRequisition).where(
            PurchaseRequisition.requestor_id == user_id
        ).order_by(desc(PurchaseRequisition.created_at)).limit(5)
        result = await self.db.execute(query)
        prs = result.scalars().all()
        return [
            {
                "id": pr.pr_number,
                "title": pr.title or "N/A",
                "amount": float(pr.total_estimated_amount or 0.0),
                "status": pr.status
            }
            for pr in prs
        ]

    async def _get_employee_my_assets(self, user_id: int) -> List[Dict[str, Any]]:
        query = select(Asset).where(
            Asset.assigned_employee_id == user_id
        ).limit(5)
        result = await self.db.execute(query)
        assets = result.scalars().all()
        return [
            {
                "id": asset.asset_id,
                "name": asset.model or asset.manufacturer or "Asset",
                "tag": asset.asset_tag or asset.asset_number,
                "status": asset.status
            }
            for asset in assets
        ]

    async def _get_employee_recent_expenses(self, user_id: int) -> List[Dict[str, Any]]:
        query = select(ExpenseReport).where(
            ExpenseReport.employee_id == user_id,
            ExpenseReport.status.in_(["Approved", "Finance Verified", "Payment Requested"])
        ).order_by(desc(ExpenseReport.created_at)).limit(5)
        result = await self.db.execute(query)
        expenses = result.scalars().all()
        return [
            {
                "id": exp.expense_report_id,
                "title": exp.purpose,
                "amount": float(exp.total_amount or 0.0),
                "date": exp.created_at.isoformat() if exp.created_at else None,
                "status": exp.status
            }
            for exp in expenses
        ]

    async def _get_category_spend(self) -> List[Dict[str, Any]]:
        # Hardcoded mockup categories or group by purchase type
        query = select(
            PurchaseRequisition.purchase_type,
            func.sum(PurchaseRequisition.total_estimated_amount).label("total_spend")
        ).group_by(PurchaseRequisition.purchase_type)
        result = await self.db.execute(query)
        return [{"category": row[0] or "Standard", "spend": float(row[1] or 0.0)} for row in result.all()]
