import asyncio
from src.database.session import async_session
from src.models.auth import User
from src.models.expense import ExpenseApproval, ExpenseReport
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name == "David", User.last_name == "Kim"))
        david = res.scalar_one_or_none()
        if not david: return
        print("David Kim user_id:", david.user_id)
        
        # Check claims assigned to David Kim via ExpenseApproval
        res = await db.execute(select(ExpenseApproval).where(ExpenseApproval.approver_id == david.user_id))
        approvals = res.scalars().all()
        print("ExpenseApprovals assigned to David:", len(approvals))
        
        # Check claims where David is the manager
        res = await db.execute(select(ExpenseReport).join(User, ExpenseReport.employee_id == User.user_id).where(User.manager_id == david.user_id))
        reports = res.scalars().all()
        print("ExpenseReports for David's reports:", [(r.expense_report_id, r.status) for r in reports])

asyncio.run(main())
