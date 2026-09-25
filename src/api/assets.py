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


def resolve_category_name(a) -> str:
    if a.category and a.category.category_name:
        return a.category.category_name
    if a.category_id == 4:
        return 'Software'
    elif a.category_id == 5:
        return 'Furniture'
    elif a.category_id in (1, 2, 3):
        return 'Hardware'
    
    name = (a.model or '').lower()
    if any(kw in name for kw in ['software', 'license', 'saas', 'app']):
        return 'Software'
    elif any(kw in name for kw in ['chair', 'desk', 'table', 'furniture', 'cabinet']):
        return 'Furniture'
    return 'Hardware'

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
            "category": resolve_category_name(a),
            "serial_number": a.serial_number or a.asset_tag,
            "purchase_date": str(a.purchase_date) if a.purchase_date else "",
            "vendor_name": a.vendor.vendor_name if a.vendor else "Unknown",
            "status": a.status
        })
        
    return mapped_assets
from src.models.assets import AssetCategory

@router.get("/categories")
async def get_asset_categories(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(AssetCategory)
    result = await session.execute(stmt)
    categories = result.scalars().all()
    return [{"id": c.category_id, "name": c.category_name, "description": c.description} for c in categories]


@router.get("")
async def get_assets(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role_name for r in current_user.roles]
    allowed = {"Admin", "CFO", "Finance Manager", "CEO"}
    if not allowed.intersection(user_roles):
        raise HTTPException(status_code=403, detail="Not authorized to view all assets")

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
            "category": resolve_category_name(a),
            "assigned_to_id": a.assigned_employee_id,
            "assigned_to_name": f"{a.assigned_employee.first_name} {a.assigned_employee.last_name}" if a.assigned_employee else "Unassigned",
            "serial_number": a.serial_number or a.asset_tag,
            "cost": float(a.cost) if a.cost else 0,
            "purchase_date": str(a.purchase_date) if a.purchase_date else "",
            "location": a.location or "HQ",
            "status": a.status
        })
        
    return mapped_assets

from src.schemas.assets import AssetCreate, AssetSchema
from fastapi import status
import uuid

@router.post("", response_model=AssetSchema, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: AssetCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Verify Admin
    user_roles = [r.role_name for r in current_user.roles]
    if "Admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only Admins can create assets manually")

    new_asset = Asset(
        asset_number=data.asset_number or str(uuid.uuid4())[:8].upper(),
        asset_tag=data.asset_tag,
        category_id=data.category_id,
        po_id=data.po_id,
        vendor_id=data.vendor_id,
        serial_number=data.serial_number,
        model=data.model,
        manufacturer=data.manufacturer,
        department_id=data.department_id,
        purchase_date=data.purchase_date,
        warranty_expiry=data.warranty_expiry,
        amc_expiry=data.amc_expiry,
        location=data.location,
        cost=data.cost,
        status=data.status or "Unassigned"
    )
    
    session.add(new_asset)
    
    history = AssetHistory(
        asset=new_asset,
        action_type="Manual Creation",
        action_by=current_user.user_id,
        details="Asset manually created by Admin."
    )
    session.add(history)
    
    await session.commit()
    
    # Reload with relationships
    stmt = select(Asset).options(
        selectinload(Asset.category),
        selectinload(Asset.assigned_employee),
        selectinload(Asset.assignments),
        selectinload(Asset.history),
        selectinload(Asset.documents)
    ).where(Asset.asset_id == new_asset.asset_id)
    result = await session.execute(stmt)
    return result.scalar_one()

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

from src.schemas.assets import AssetUpdate
@router.put("/{asset_id}", response_model=AssetSchema)
async def update_asset(
    asset_id: int,
    data: AssetUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role_name for r in current_user.roles]
    if "Admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only Admins can update assets")

    stmt = select(Asset).where(Asset.asset_id == asset_id)
    result = await session.execute(stmt)
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if data.model is not None:
        asset.model = data.model
    if data.category_id is not None:
        asset.category_id = data.category_id
    if data.status is not None:
        asset.status = data.status
    if data.location is not None:
        asset.location = data.location
    if data.warranty_expiry is not None:
        asset.warranty_expiry = data.warranty_expiry
    if data.amc_expiry is not None:
        asset.amc_expiry = data.amc_expiry
    if data.cost is not None:
        asset.cost = data.cost
        
    # we might also want to update model, category_id if provided. For simplicity, just adding cost here. Wait, AssetUpdate only has status, location, etc. Let's add model and category_id in AssetUpdate schema? The prompt requires editing name, category, cost, status.
    # Actually, I should update AssetUpdate schema to include model and category_id.
    
    await session.commit()
    
    # Reload
    stmt = select(Asset).options(
        selectinload(Asset.category),
        selectinload(Asset.assigned_employee),
        selectinload(Asset.assignments),
        selectinload(Asset.history),
        selectinload(Asset.documents)
    ).where(Asset.asset_id == asset_id)
    res = await session.execute(stmt)
    return res.scalar_one()
