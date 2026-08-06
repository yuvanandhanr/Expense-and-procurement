import os
import sys
import asyncio
import csv
from datetime import datetime
import kagglehub
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.database.session import async_session
from src.models.auth import User
from src.models.organization import Department
from src.models.vendor import Vendor, VendorPerformance
from src.models.purchase_requisition import PurchaseRequisition, PRItem
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from src.models.delivery import Delivery, DeliveryItem
from src.models.grn import GoodsReceipt, GoodsReceiptItem
from decimal import Decimal

async def get_or_create_vendor(session, supplier_name: str) -> Vendor:
    # Check if vendor exists
    result = await session.execute(
        text("SELECT vendor_id FROM vendors WHERE vendor_name = :name"), 
        {"name": supplier_name}
    )
    vendor_id = result.scalar()
    
    if vendor_id:
        return vendor_id
        
    # Create new vendor
    vendor_code = f"VEND-{uuid.uuid4().hex[:6].upper()}"
    new_vendor = Vendor(
        vendor_code=vendor_code,
        vendor_name=supplier_name,
        email=f"sales@{supplier_name.lower().replace(' ', '')}.com",
        status="Active"
    )
    session.add(new_vendor)
    await session.flush()
    return new_vendor.vendor_id

async def seed_data():
    path = kagglehub.dataset_download('shahriarkabir/procurement-kpi-analysis-dataset')
    
    csv_file = None
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith('.csv'):
                csv_file = os.path.join(root, f)
                break
                
    if not csv_file:
        print("No CSV found in dataset!")
        return

    print(f"Reading dataset from {csv_file}...")

    async with async_session() as session:
        # Get defaults
        result = await session.execute(text("SELECT user_id FROM users LIMIT 1"))
        admin_id = result.scalar() or 1
        
        result = await session.execute(text("SELECT department_id FROM departments LIMIT 1"))
        dept_id = result.scalar() or 1

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            count = 0
            for row in reader:
                po_number = row['PO_ID']
                supplier = row['Supplier']
                
                order_date = datetime.strptime(row['Order_Date'], '%Y-%m-%d') if row['Order_Date'] else datetime.utcnow()
                delivery_date = datetime.strptime(row['Delivery_Date'], '%Y-%m-%d') if row['Delivery_Date'] else None
                
                category = row['Item_Category']
                status = row['Order_Status']
                quantity = int(float(row['Quantity']))
                unit_price = Decimal(row['Unit_Price'])
                negotiated_price = Decimal(row['Negotiated_Price']) if row['Negotiated_Price'] else unit_price
                defective_units = int(float(row['Defective_Units'])) if row['Defective_Units'] else 0
                compliance = row['Compliance']
                
                vendor_id = await get_or_create_vendor(session, supplier)
                
                total_estimated_amount = unit_price * quantity
                grand_total = negotiated_price * quantity
                
                # 1. PR
                pr_number = f"PR-{po_number.split('-')[1]}"
                pr = PurchaseRequisition(
                    pr_number=pr_number,
                    title=f"Kaggle Order {po_number}",
                    justification="Historical Dataset",
                    total_estimated_amount=total_estimated_amount,
                    priority="Medium",
                    requestor_id=admin_id,
                    department_id=dept_id,
                    status="Approved",
                    created_at=order_date
                )
                session.add(pr)
                await session.flush()
                
                pr_item = PRItem(
                    pr_id=pr.pr_id,
                    category=category,
                    item_name=f"{category} Bulk",
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_estimated_amount
                )
                session.add(pr_item)
                
                # 2. PO
                po = PurchaseOrder(
                    po_number=po_number,
                    pr_id=pr.pr_id,
                    vendor_id=vendor_id,
                    department_id=dept_id,
                    total_amount=grand_total,
                    grand_total=grand_total,
                    status=status if status in ["Issued", "Completed", "Cancelled", "Draft"] else "Issued",
                    created_by=admin_id,
                    created_at=order_date
                )
                session.add(po)
                await session.flush()
                
                po_item = PurchaseOrderItem(
                    po_id=po.po_id,
                    item_name=f"{category} Bulk",
                    quantity=quantity,
                    unit_price=negotiated_price,
                    total_price=grand_total
                )
                session.add(po_item)
                await session.flush()
                
                # 3. Delivery
                if delivery_date and status != "Cancelled":
                    delivery = Delivery(
                        po_id=po.po_id,
                        vendor_id=vendor_id,
                        delivery_number=f"DEL-{po_number.split('-')[1]}",
                        delivery_date=delivery_date,
                        status="Delivered",
                        created_at=delivery_date
                    )
                    session.add(delivery)
                    await session.flush()
                    
                    delivery_item = DeliveryItem(
                        delivery_id=delivery.delivery_id,
                        po_item_id=po_item.po_item_id,
                        item_name=po_item.item_name,
                        quantity_shipped=quantity
                    )
                    session.add(delivery_item)
                    await session.flush()
                    
                    # 4. GRN
                    grn = GoodsReceipt(
                        grn_number=f"GRN-{po_number.split('-')[1]}",
                        po_id=po.po_id,
                        vendor_id=vendor_id,
                        delivery_id=delivery.delivery_id,
                        received_by=admin_id,
                        received_date=delivery_date,
                        status="Completed",
                        created_at=delivery_date
                    )
                    session.add(grn)
                    await session.flush()
                    
                    grn_item = GoodsReceiptItem(
                        grn_id=grn.grn_id,
                        delivery_item_id=delivery_item.delivery_item_id,
                        quantity_received=quantity - defective_units,
                        quantity_rejected=defective_units
                    )
                    session.add(grn_item)
                
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count} rows...")
                    await session.commit()
            
            await session.commit()
            print(f"Successfully seeded {count} rows from Kaggle Dataset!")

if __name__ == "__main__":
    asyncio.run(seed_data())
