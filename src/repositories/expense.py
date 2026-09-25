from typing import Optional, List, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.auth import User
from src.models.expense import ExpenseReport, Receipt, ExpenseApproval


class ExpenseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_reports(self, employee_id: Optional[int] = None, department_id: Optional[int] = None) -> Sequence[ExpenseReport]:
        stmt = select(ExpenseReport).options(
            selectinload(ExpenseReport.receipts),
            selectinload(ExpenseReport.approvals),
            selectinload(ExpenseReport.employee).selectinload(User.roles)
        )
        if employee_id:
            stmt = stmt.where(ExpenseReport.employee_id == employee_id)
        if department_id:
            stmt = stmt.where(ExpenseReport.department_id == department_id)
        stmt = stmt.order_by(ExpenseReport.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_report_by_id(self, report_id: int) -> Optional[ExpenseReport]:
        stmt = select(ExpenseReport).options(
            selectinload(ExpenseReport.receipts),
            selectinload(ExpenseReport.approvals),
            selectinload(ExpenseReport.employee).selectinload(User.roles)
        ).where(ExpenseReport.expense_report_id == report_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_report(self, report: ExpenseReport) -> ExpenseReport:
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def update_report(self, report: ExpenseReport) -> ExpenseReport:
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def delete_report(self, report: ExpenseReport) -> None:
        await self.db.delete(report)
        await self.db.flush()

    # Receipt operations
    async def add_receipt(self, receipt: Receipt) -> Receipt:
        self.db.add(receipt)
        await self.db.flush()
        await self.db.refresh(receipt)
        return receipt

    async def get_receipt_by_id(self, receipt_id: int) -> Optional[Receipt]:
        stmt = select(Receipt).where(Receipt.receipt_id == receipt_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_receipt_by_content_hash(self, report_id: int, content_hash: str) -> Optional[Receipt]:
        stmt = select(Receipt).where(
            Receipt.expense_report_id == report_id,
            Receipt.content_hash == content_hash,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
        
    async def get_receipts_by_report(self, report_id: int) -> Sequence[Receipt]:
        stmt = select(Receipt).where(Receipt.expense_report_id == report_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_receipt(self, receipt: Receipt) -> Receipt:
        await self.db.flush()
        await self.db.refresh(receipt)
        return receipt

    async def delete_receipt(self, receipt: Receipt) -> None:
        await self.db.delete(receipt)
        await self.db.flush()
