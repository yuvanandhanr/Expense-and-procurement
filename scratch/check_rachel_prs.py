import asyncio
from src.database.session import async_session
from src.models.auth import User
from src.models.purchase_requisition import PurchaseRequisition
from sqlalchemy import select

async def main():
    async with async_session() as db:
        res = await db.execute(select(User).where(User.first_name == "Rachel"))
        rachel = res.scalar_one_or_none()
        if rachel:
            res_pr = await db.execute(select(PurchaseRequisition).where(PurchaseRequisition.requestor_id == rachel.user_id))
            prs = res_pr.scalars().all()
            print(f"Rachel PRs: {len(prs)}")

asyncio.run(main())
