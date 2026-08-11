from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.models.assets import Asset, AssetAssignment, AssetHistory

class TransferRequest(BaseModel):
    new_employee_id: int
    notes: Optional[str] = None

router = APIRouter(prefix="/assets", tags=["Assets"])
@router.get("/my-assets")
async def get_my_assets(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Asset).options(
        selectinload(Asset.category),
        selectinload(Asset.assigned_employee),
        selectinload(Asset.vendor)
    ).where(Asset.assigned_employee_id == current_user.user_id)
    
    result = await session.execute(stmt)
    assets = result.scalars().all()
    
    mapped_assets = []
    for a in assets:
        mapped_assets.append({
            "asset_id": a.asset_id,
            "asset_code": a.asset_number,
            "asset_name": a.model or "Hardware Asset",
            "category": a.category.category_name if a.category else "Uncategorized",
            "serial_number": a.serial_number,
            "purchase_date": str(a.purchase_date) if a.purchase_date else "",
            "vendor_name": a.vendor.vendor_name if a.vendor else "Unknown",
            "status": a.status
        })
        
    return mapped_assets

@router.get("")
async def get_assets(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Asset).options(
        selectinload(Asset.category),
        selectinload(Asset.assigned_employee)
    )
    result = await session.execute(stmt)
    assets = result.scalars().all()
    
    # Map to frontend expected shape
    mapped_assets = []
    for a in assets:
        mapped_assets.append({
            "asset_id": a.asset_id,
            "asset_code": a.asset_number,
            "asset_name": a.model or "Generic Asset",
            "category": a.category.category_name if a.category else "Uncategorized",
            "assigned_to_id": a.assigned_employee_id,
            "assigned_to_name": f"{a.assigned_employee.first_name} {a.assigned_employee.last_name}" if a.assigned_employee else "Unassigned",
            "serial_number": a.serial_number,
            "cost": 0, # Could be fetched from PO if joined
            "purchase_date": str(a.purchase_date) if a.purchase_date else "",
            "location": a.location or "HQ",
            "status": a.status
        })
        
    return mapped_assets

@router.post("/{asset_id}/transfer")
async def transfer_asset(
    asset_id: int,
    data: TransferRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Verify Admin
    user_roles = [r.role_name for r in current_user.roles]
    if "Admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only Admins can transfer assets")

    # Fetch Asset
    stmt = select(Asset).options(selectinload(Asset.assignments)).where(Asset.asset_id == asset_id)
    result = await session.execute(stmt)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    today = date.today()

    # End current active assignments
    for assignment in asset.assignments:
        if assignment.status == "Active":
            assignment.return_date = today
            assignment.status = "Transferred"
            if data.notes:
                assignment.notes = f"{assignment.notes or ''}\nTransfer note: {data.notes}"

    # Create new assignment
    new_assignment = AssetAssignment(
        asset_id=asset.asset_id,
        assigned_to=data.new_employee_id,
        assigned_by=current_user.user_id,
        assigned_date=today,
        status="Active",
        notes=data.notes
    )
    session.add(new_assignment)

    # Update Asset
    asset.assigned_employee_id = data.new_employee_id
    asset.status = "Assigned"

    # Add History
    history = AssetHistory(
        asset_id=asset.asset_id,
        action_type="Transfer",
        action_by=current_user.user_id,
        details=f"Transferred to employee ID {data.new_employee_id}. Notes: {data.notes or ''}"
    )
    session.add(history)

    await session.commit()
    return {"message": "Asset transferred successfully"}
