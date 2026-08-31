import asyncio
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.core.config import settings
from src.models.vendor import Vendor, VendorPerformance
from src.models.rfq import RequestForQuotation, RFQItem
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from src.models.grn import GoodsReceipt, GoodsReceiptItem
from src.models.invoice import VendorInvoice, InvoiceItem

async def seed_vendor_data():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Check if Test Vendor exists
        result = await session.execute(select(Vendor).where(Vendor.vendor_code == "VEND-001"))
        vendor = result.scalar_one_or_none()
        if not vendor:
            print("Creating Test Vendor...")
            vendor = Vendor(
                vendor_code="VEND-001",
                vendor_name="Test Vendor",
                legal_name="Test Vendor LLC",
                email="vendor@dataeko.ai",
                phone="123-456-7890",
                status="Active"
            )
            session.add(vendor)
            await session.flush()
            
            perf = VendorPerformance(
                vendor_id=vendor.vendor_id,
                delivery_performance=Decimal("95.50"),
                quality_score=Decimal("100.00"),
                response_time=Decimal("98.00"),
                contract_compliance=Decimal("100.00"),
                purchase_volume=Decimal("50000.00"),
                avg_lead_time_days=Decimal("5.00"),
                rating=Decimal("4.80")
            )
            session.add(perf)
            await session.flush()
        else:
            print("Test Vendor already exists.")

        vendor_id = vendor.vendor_id

        # Seed an RFQ
        print("Seeding RFQ...")
        rfq = RequestForQuotation(
            pr_id=None,
            rfq_number="RFQ-2026-001",
            title="Office Equipment Supply",
            status="Open",
            submission_deadline=datetime.utcnow() + timedelta(days=7),
            description="Please provide best rates for office chairs and desks."
        )
        session.add(rfq)
        await session.flush()
        
        rfq_item1 = RFQItem(
            rfq_id=rfq.rfq_id,
            pr_item_id=None,
            item_name="Ergonomic Office Chair",
            quantity=10
        )
        rfq_item2 = RFQItem(
            rfq_id=rfq.rfq_id,
            pr_item_id=None,
            item_name="Standing Desk",
            quantity=5
        )
        session.add_all([rfq_item1, rfq_item2])
        await session.flush()

        from src.models.rfq import RFQVendor
        rfq_vendor = RFQVendor(
            rfq_id=rfq.rfq_id,
            vendor_id=vendor_id
        )
        session.add(rfq_vendor)
        await session.flush()

        # Seed a Purchase Order for the Vendor
        print("Seeding Purchase Order...")
        po = PurchaseOrder(
            po_number="PO-2026-001",
            vendor_id=vendor_id,
            total_amount=Decimal("12500.00"),
            grand_total=Decimal("12500.00"),
            status="Approved",
            created_by=1
        )
        session.add(po)
        await session.flush()

        po_item1 = PurchaseOrderItem(
            po_id=po.po_id,
            item_name="MacBook Pro M3",
            quantity=5,
            unit_price=Decimal("2500.00"),
            total_price=Decimal("12500.00")
        )
        session.add(po_item1)
        await session.flush()

        # Seed a GRN
        print("Seeding GRN...")
        grn = GoodsReceipt(
            po_id=po.po_id,
            grn_number="GRN-2026-001",
            received_date=datetime.utcnow(),
            received_by=1,
            status="Completed"
        )
        session.add(grn)
        await session.flush()
        
        grn_item1 = GoodsReceiptItem(
            grn_id=grn.grn_id,
            quantity_received=5,
            quantity_rejected=0
        )
        session.add(grn_item1)

        # Seed a Vendor Invoice
        print("Seeding Vendor Invoice...")
        invoice = VendorInvoice(
            vendor_id=vendor_id,
            po_id=po.po_id,
            invoice_number="INV-2026-001",
            invoice_date=datetime.utcnow().date(),
            subtotal=Decimal("12500.00"),
            grand_total=Decimal("12500.00"),
            taxes=Decimal("0.00"),
            status="Pending Approval"
        )
        session.add(invoice)
        await session.flush()
        
        invoice_item1 = InvoiceItem(
            invoice_id=invoice.invoice_id,
            item_name="MacBook Pro M3",
            quantity=5,
            unit_price=Decimal("2500.00"),
            total_price=Decimal("12500.00")
        )
        session.add(invoice_item1)

        await session.commit()
        print("Vendor mock data seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_vendor_data())
