import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.models.invoice import VendorInvoice

async def list_invoices():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        stmt = select(VendorInvoice).order_by(VendorInvoice.created_at.desc())
        result = await session.execute(stmt)
        invoices = result.scalars().all()
        for inv in invoices:
            print(f"Invoice ID: {inv.invoice_id}, Number: {inv.invoice_number}, Vendor: {inv.vendor_id}, Employee: {inv.employee_id}, Amount: {inv.amount}, Grand Total: {inv.grand_total}")

if __name__ == "__main__":
    asyncio.run(list_invoices())
