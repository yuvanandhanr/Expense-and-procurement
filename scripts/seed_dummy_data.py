import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.database.session import async_session
from src.models.auth import User
from src.models.organization import Department
from src.models.vendor import Vendor
from src.models.purchase_requisition import PurchaseRequisition
from src.models.purchase_order import PurchaseOrder
import random

async def seed_data():
    async with async_session() as session:
        # Check if dummy data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM purchase_requisitions"))
        if result.scalar() > 0:
            print("Database already contains data. Skipping seeder.")
            return

        print("Seeding dummy data...")
        
        # Insert Vendors
        vendors = [
            Vendor(vendor_code="VEND-001", vendor_name="TechCorp Supplies", email="sales@techcorp.com", phone="555-0101", address="123 Tech Ln", status="Active"),
            Vendor(vendor_code="VEND-002", vendor_name="Office World", email="orders@officeworld.com", phone="555-0202", address="456 Office Rd", status="Active"),
            Vendor(vendor_code="VEND-003", vendor_name="Global Logistics", email="support@globallogistics.com", phone="555-0303", address="789 Ship Blvd", status="Active"),
            Vendor(vendor_code="VEND-004", vendor_name="Cyber Shield Sec", email="info@cybershield.com", phone="555-0404", address="101 Sec Ave", status="Active"),
            Vendor(vendor_code="VEND-005", vendor_name="Paper Co", email="sales@paperco.com", phone="555-0505", address="202 Paper St", status="Inactive")
        ]
        session.add_all(vendors)
        await session.flush()

        # Get the Admin user (usually user_id = 1)
        result = await session.execute(text("SELECT user_id FROM users LIMIT 1"))
        admin_id = result.scalar()
        if not admin_id:
            admin_id = 1

        # Get Department 1
        result = await session.execute(text("SELECT department_id FROM departments LIMIT 1"))
        dept_id = result.scalar()
        if not dept_id:
            dept_id = 1

        # Insert Purchase Requisitions
        prs = [
            PurchaseRequisition(pr_number="PR-001", title="Q3 Server Upgrades", description="Need new servers for AI division", justification="Capacity limits reached", total_estimated_amount=150000, priority="High", requestor_id=admin_id, department_id=dept_id, status="Approved"),
            PurchaseRequisition(pr_number="PR-002", title="Office Chairs", description="Ergonomic chairs for new hires", justification="Employee comfort", total_estimated_amount=5000, priority="Medium", requestor_id=admin_id, department_id=dept_id, status="Submitted"),
            PurchaseRequisition(pr_number="PR-003", title="Cloud Subscription", description="Annual AWS bill", justification="Infrastructure", total_estimated_amount=75000, priority="High", requestor_id=admin_id, department_id=dept_id, status="Draft"),
            PurchaseRequisition(pr_number="PR-004", title="Marketing Materials", description="Brochures and banners for event", justification="Q4 campaign", total_estimated_amount=2500, priority="Low", requestor_id=admin_id, department_id=dept_id, status="Rejected"),
            PurchaseRequisition(pr_number="PR-005", title="Developer Laptops", description="5 Macbook Pros", justification="New hires", total_estimated_amount=12500, priority="Medium", requestor_id=admin_id, department_id=dept_id, status="Approved")
        ]
        session.add_all(prs)
        await session.flush()

        # Insert Purchase Orders
        pos = [
            PurchaseOrder(po_number="PO-2026-001", pr_id=prs[0].pr_id, vendor_id=vendors[0].vendor_id, total_amount=145000, grand_total=145000, status="Issued", created_by=admin_id),
            PurchaseOrder(po_number="PO-2026-002", pr_id=prs[4].pr_id, vendor_id=vendors[0].vendor_id, total_amount=12500, grand_total=12500, status="Completed", created_by=admin_id),
            PurchaseOrder(po_number="PO-2026-003", pr_id=prs[1].pr_id, vendor_id=vendors[1].vendor_id, total_amount=4800, grand_total=4800, status="Draft", created_by=admin_id)
        ]
        session.add_all(pos)
        
        await session.commit()
        print("Dummy data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
