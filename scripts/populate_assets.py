import asyncio
import uuid
import random
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import select

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.session import async_session
from src.models.auth import User
from src.models.assets import Asset, AssetCategory, AssetAssignment
from src.models.vendor import Vendor
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from src.models.delivery import Delivery, DeliveryItem

async def populate():
    async with async_session() as session:
        # 1. Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        # 2. Ensure Vendor exists
        result = await session.execute(select(Vendor).filter_by(vendor_code="VEND-001"))
        vendor = result.scalars().first()
        if not vendor:
            vendor = Vendor(
                vendor_code="VEND-001",
                name="Apex Technologies",
                email="contact@apextech.com",
                status="Active"
            )
            session.add(vendor)
            await session.commit()
            
        # 3. Ensure Asset Categories exist
        result = await session.execute(select(AssetCategory).filter_by(category_name="Laptop"))
        laptop_cat = result.scalars().first()
        if not laptop_cat:
            laptop_cat = AssetCategory(category_name="Laptop", description="Computers")
            session.add(laptop_cat)
            
        result = await session.execute(select(AssetCategory).filter_by(category_name="Monitor"))
        monitor_cat = result.scalars().first()
        if not monitor_cat:
            monitor_cat = AssetCategory(category_name="Monitor", description="Displays")
            session.add(monitor_cat)
            
        await session.commit()
        
        # 4. Generate assets and deliveries
        base_date = datetime.utcnow() - timedelta(days=60)
        
        for idx, user in enumerate(users):
            po_num = f"PO-AST-{uuid.uuid4().hex[:6].upper()}"
            delivery_num = f"DEL-AST-{uuid.uuid4().hex[:6].upper()}"
            purchase_dt = base_date + timedelta(days=random.randint(1, 40))
            
            # Create a PO for this user's assets
            po = PurchaseOrder(
                po_number=po_num,
                vendor_id=vendor.vendor_id,
                status="Delivered",
                delivery_date=purchase_dt,
                total_amount=2500.0,
                grand_total=2500.0,
                created_by=user.user_id,
                department_id=user.department_id
            )
            session.add(po)
            await session.flush()
            
            # PO Items
            po_item_laptop = PurchaseOrderItem(
                po_id=po.po_id,
                item_name=f"MacBook Pro 16 - {user.first_name}",
                quantity=1,
                unit_price=2000.0,
                total_price=2000.0
            )
            po_item_monitor = PurchaseOrderItem(
                po_id=po.po_id,
                item_name=f"Dell UltraSharp 27 - {user.first_name}",
                quantity=1,
                unit_price=500.0,
                total_price=500.0
            )
            session.add_all([po_item_laptop, po_item_monitor])
            await session.flush()
            
            # Create a Delivery for the Vendor Portal
            delivery = Delivery(
                po_id=po.po_id,
                vendor_id=vendor.vendor_id,
                delivery_number=delivery_num,
                delivery_date=purchase_dt,
                expected_date=purchase_dt,
                status="Delivered"
            )
            session.add(delivery)
            await session.flush()
            
            # Delivery Items
            del_item_laptop = DeliveryItem(
                delivery_id=delivery.delivery_id,
                po_item_id=po_item_laptop.po_item_id,
                item_name=po_item_laptop.item_name,
                quantity_shipped=1
            )
            del_item_monitor = DeliveryItem(
                delivery_id=delivery.delivery_id,
                po_item_id=po_item_monitor.po_item_id,
                item_name=po_item_monitor.item_name,
                quantity_shipped=1
            )
            session.add_all([del_item_laptop, del_item_monitor])
            await session.flush()
            
            # Create Assets
            laptop_asset = Asset(
                asset_number=f"AST-L-{uuid.uuid4().hex[:6].upper()}",
                asset_tag=f"TAG-L-{uuid.uuid4().hex[:6].upper()}",
                category_id=laptop_cat.category_id,
                po_id=po.po_id,
                vendor_id=vendor.vendor_id,
                model="MacBook Pro 16",
                manufacturer="Apple",
                department_id=user.department_id,
                assigned_employee_id=user.user_id,
                purchase_date=purchase_dt.date(),
                status="Assigned"
            )
            
            monitor_asset = Asset(
                asset_number=f"AST-M-{uuid.uuid4().hex[:6].upper()}",
                asset_tag=f"TAG-M-{uuid.uuid4().hex[:6].upper()}",
                category_id=monitor_cat.category_id,
                po_id=po.po_id,
                vendor_id=vendor.vendor_id,
                model="Dell UltraSharp 27",
                manufacturer="Dell",
                department_id=user.department_id,
                assigned_employee_id=user.user_id,
                purchase_date=purchase_dt.date(),
                status="Assigned"
            )
            session.add_all([laptop_asset, monitor_asset])
            await session.flush()

            # Create Asset Assignments
            lap_assignment = AssetAssignment(
                asset_id=laptop_asset.asset_id,
                assigned_to=user.user_id,
                assigned_date=purchase_dt.date(),
                status="Active"
            )
            mon_assignment = AssetAssignment(
                asset_id=monitor_asset.asset_id,
                assigned_to=user.user_id,
                assigned_date=purchase_dt.date(),
                status="Active"
            )
            session.add_all([lap_assignment, mon_assignment])
            
        await session.commit()
        print(f"Successfully created assets and deliveries for {len(users)} users.")

if __name__ == "__main__":
    asyncio.run(populate())
