from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timezone, date, datetime
from typing import Optional, List
import uuid
from sqlalchemy import select

from src.models.assets import Asset, AssetAssignment, AssetHistory

class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_assets_from_grn(
        self,
        po_id: int,
        vendor_id: int,
        item_name: str,
        quantity: int,
        serial_numbers: Optional[str] = None,
        requestor_id: Optional[int] = None
    ) -> List[Asset]:
        assets = []
        today = date.today()
        
        sn_list = []
        if serial_numbers:
            sn_list = [sn.strip() for sn in serial_numbers.split(",") if sn.strip()]
        
        for i in range(quantity):
            # Generate a generic asset tag if not provided
            asset_tag = f"AST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{i}"
            sn = sn_list[i] if i < len(sn_list) else None

            status = "Assigned" if requestor_id else "In Stock"

            asset = Asset(
                asset_tag=asset_tag,
                asset_number=f"AN-{uuid.uuid4().hex[:6].upper()}",
                serial_number=sn,
                model=item_name,
                purchase_date=today,
                vendor_id=vendor_id,
                status=status,
                assigned_employee_id=requestor_id if requestor_id else None
            )
            self.db.add(asset)
            await self.db.flush() # flush to get asset_id

            # Add History
            history = AssetHistory(
                asset_id=asset.asset_id,
                action_type="Received",
                action_by=None, # System action
                details=f"Received via GRN for PO {po_id}"
            )
            self.db.add(history)

            # If requestor exists, assign it automatically
            if requestor_id:
                assignment = AssetAssignment(
                    asset_id=asset.asset_id,
                    assigned_to=requestor_id,
                    assigned_by=None, # System assignment
                    assigned_date=today,
                    status="Active",
                    notes=f"Auto-assigned from PO {po_id} GRN"
                )
                self.db.add(assignment)
                
                assign_history = AssetHistory(
                    asset_id=asset.asset_id,
                    action_type="Assigned",
                    action_by=None, # System action
                    details=f"Auto-assigned to requestor {requestor_id} from GRN"
                )
                self.db.add(assign_history)
                
            assets.append(asset)
            
        await self.db.flush()
        return assets
