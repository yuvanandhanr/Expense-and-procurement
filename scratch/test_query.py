import asyncio
from src.database.config import async_session
from src.models.auth import User, Role
from src.models.expense import ExpenseReport, ExpenseApproval
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

async def main():
    async with async_session() as db:
        user_roles = ["Manager"]
        is_pure_manager = True
        
        stmt = select(ExpenseReport).options(
            selectinload(ExpenseReport.receipts),
            selectinload(ExpenseReport.approvals),
            selectinload(ExpenseReport.employee).selectinload(User.roles)
        ).join(User, ExpenseReport.employee_id == User.user_id).outerjoin(
            ExpenseApproval, ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id
        )

        manager_cond = (User.manager_id == 1) & (ExpenseReport.status != 'Draft')
        if is_pure_manager:
            manager_cond = manager_cond & (~User.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))

        conditions = [
            ExpenseReport.employee_id == 1,
            manager_cond,
            (ExpenseApproval.approver_id == 1) & (ExpenseReport.status != 'Draft')
        ]

        stmt = stmt.where(or_(*conditions)).order_by(ExpenseReport.created_at.desc())
        print("Query built, executing...")
        try:
            result = await db.execute(stmt)
            print("Success")
        except Exception as e:
            print("Error:", e)

asyncio.run(main())
