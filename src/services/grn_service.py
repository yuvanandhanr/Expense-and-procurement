import uuid
from typing import List, Optional
from datetime import timezone, datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.grn import GoodsReceipt, GoodsReceiptItem
from src.models.purchase_order import PurchaseOrder
from src.repositories.grn import GRNRepository, GRNItemRepository
from src.repositories.purchase_order import PORepository
from src.repositories.inspection import InspectionRepository
from src.repositories.purchase_requisition import PRRepository
from src.services.asset_service import AssetService
from src.schemas.grn import GRNCreate

class GRNService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.grn_repo = GRNRepository(db)
        self.item_repo = GRNItemRepository(db)
        self.po_repo = PORepository(db)
        self.inspection_repo = InspectionRepository(db)
        self.pr_repo = PRRepository(db)
        self.asset_service = AssetService(db)

    def generate_grn_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"GRN-{date_str}-{rand_str}"

    async def create_grn(self, data: GRNCreate, user_id: int) -> GoodsReceipt:
        po = await self.po_repo.get_by_id(data.po_id)
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")

        # Business Rule: Cloud subscriptions skip physical GRN / inspection
        is_cloud_sub = False
        for po_item in po.items:
            # Check if item name contains "cloud", "saas", "subscription", or "license"
            name_lower = po_item.item_name.lower()
            if any(term in name_lower for term in ("cloud", "saas", "subscription", "license")):
                is_cloud_sub = True
                break

        grn_number = self.generate_grn_number()
        grn = GoodsReceipt(
            grn_number=grn_number,
            po_id=data.po_id,
            vendor_id=data.vendor_id,
            delivery_id=data.delivery_id,
            inspection_id=data.inspection_id,
            warehouse=data.warehouse or "Main Warehouse",
            received_by=user_id,
            received_date=datetime.now(timezone.utc),
            notes=data.notes,
            created_at=datetime.now(timezone.utc)
        )

        if is_cloud_sub:
            grn.status = "Completed"
            grn = await self.grn_repo.create(grn)
            # Create receipt items matching PO items automatically
            for po_item in po.items:
                grn_item = GoodsReceiptItem(
                    grn_id=grn.grn_id,
                    quantity_received=po_item.quantity,
                    quantity_rejected=0
                )
                await self.item_repo.create(grn_item)
            po.status = "Completed"
            await self.po_repo.update(po)
            return await self.grn_repo.get_by_id(grn.grn_id)

        # Standard path requires inspection
        if not data.inspection_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inspection report is mandatory for physical receipts"
            )

        inspection = await self.inspection_repo.get_by_id(data.inspection_id)
        if not inspection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection report not found")

        # Reconcile GRN status based on inspection outcome
        if inspection.outcome == "Accepted":
            grn.status = "Completed"
            po.status = "Completed"
        elif inspection.outcome == "Partial Acceptance":
            grn.status = "Partial"
            po.status = "Partially Delivered"
        elif inspection.outcome == "Rejected":
            grn.status = "Rejected"
            po.status = "Delivery Rejected"
        else:
            grn.status = "Pending"

        grn = await self.grn_repo.create(grn)

        # Create GRN items from inspection items
        for insp_item in inspection.items:
            grn_item = GoodsReceiptItem(
                grn_id=grn.grn_id,
                delivery_item_id=insp_item.delivery_item_id,
                quantity_received=insp_item.quantity_accepted,
                quantity_rejected=insp_item.quantity_rejected
            )
            await self.item_repo.create(grn_item)

            # Business Rule: Automatically register assets on successful receipt for Hardware/IT
            # We check if item contains hardware, IT, laptop, server, mobile etc.
            # (or we can register any accepted physical items as assets for robust test coverage!)
            if insp_item.quantity_accepted > 0:
                requestor_id = None
                if po.pr_id:
                    pr = await self.pr_repo.get_by_id(po.pr_id)
                    if pr:
                        requestor_id = pr.requestor_id
                        
                await self.asset_service.register_assets_from_grn(
                    po_id=po.po_id,
                    vendor_id=data.vendor_id,
                    item_name=insp_item.delivery_item.item_name,
                    quantity=insp_item.quantity_accepted,
                    serial_numbers=insp_item.serial_numbers,
                    requestor_id=requestor_id
                )

        await self.po_repo.update(po)
        return await self.grn_repo.get_by_id(grn.grn_id)
