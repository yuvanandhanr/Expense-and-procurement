import asyncio
from src.database.session import async_session
from src.models.auth import User as UserModel
from src.models.expense import ExpenseReport, ExpenseApproval
from sqlalchemy.orm import selectinload
from sqlalchemy import select

async def test():
    async with async_session() as db:
        stmt = (
            select(ExpenseReport, UserModel)
            .options(selectinload(UserModel.roles))
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)
            .join(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id))
            .where(
                ExpenseReport.status != "Draft",
                ExpenseApproval.approver_id == 1,
                ExpenseApproval.status == "Pending"
            )
        )
        try:
            result = await db.execute(stmt)
            print("OK")
        except Exception as e:
            print("ERROR", repr(e))

asyncio.run(test())
