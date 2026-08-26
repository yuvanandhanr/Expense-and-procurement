from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date
from decimal import Decimal

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.models.assets import Asset, AssetIncident, AssetCategory
from src.schemas.assets import AssetIncidentCreate, AssetIncidentAction, AssetIncidentSchema
from src.services.pr_service import PRService
from src.schemas.purchase_requisition import PRCreate, PRItemCreate

router = APIRouter(prefix="/asset-incidents", tags=["Asset Incidents"])


@router.post("", response_model=AssetIncidentSchema, status_code=status.HTTP_201_CREATED)
async def report_incident(
    data: AssetIncidentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Check if asset belongs to user
    stmt = select(Asset).where(Asset.asset_id == data.asset_id)
    result = await session.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.assigned_employee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only report incidents on your assigned assets")

    incident = AssetIncident(
        asset_id=data.asset_id,
        reporter_id=current_user.user_id,
        description=data.description,
        incident_type=data.incident_type,
        status="Reported"
    )
    
    asset.status = "Damaged" if data.incident_type == "Damage" else "Reported"

    session.add(incident)
    await session.commit()
    await session.refresh(incident)

    return incident


@router.get("", response_model=List[AssetIncidentSchema])
async def list_incidents(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role_name for r in current_user.roles]
    
    if any(r in user_roles for r in ["Admin", "IT", "CEO", "CFO"]):
        stmt = select(AssetIncident)
    elif "Manager" in user_roles:
        stmt = select(AssetIncident).join(Asset).where(Asset.department_id == current_user.department_id)
    else:
        stmt = select(AssetIncident).where(AssetIncident.reporter_id == current_user.user_id)

    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/{incident_id}/action", response_model=AssetIncidentSchema)
async def action_incident(
    incident_id: int,
    data: AssetIncidentAction,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role_name for r in current_user.roles]
    
    stmt = select(AssetIncident).options(selectinload(AssetIncident.asset)).where(AssetIncident.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if data.action == "Approve" and incident.status == "Reported":
        if "Manager" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Managers can approve inspections")
        incident.status = "Inspection Pending"
        incident.resolution = data.resolution

    elif data.action == "Reject" and incident.status == "Reported":
        if "Manager" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Managers can reject reports")
        incident.status = "Rejected"
        incident.resolution = data.resolution
        incident.asset.status = "Assigned" # Revert asset status

    elif data.action == "Repair" and incident.status == "Inspection Pending":
        if "IT" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only IT/Admin can log repairs")
        incident.status = "Repair"
        incident.resolution = data.resolution
        incident.asset.status = "Under Maintenance"

    elif data.action == "Replace" and incident.status == "Inspection Pending":
        if "IT" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only IT/Admin can log replacements")
        incident.status = "Replacement"
        incident.resolution = data.resolution
        incident.asset.status = "Disposed"
        
        # End current assignment
        from src.models.assets import AssetAssignment
        from datetime import date
        for assignment in incident.asset.assignments:
            if assignment.status == "Active":
                assignment.status = "Returned"
                assignment.return_date = date.today()
        
        old_employee_id = incident.asset.assigned_employee_id
        incident.asset.assigned_employee_id = None # Assignment ended

        # Automatically create PR for replacement
        pr_service = PRService(session)
        
        # Fetch category name to use for PR item
        cat_stmt = select(AssetCategory).where(AssetCategory.category_id == incident.asset.category_id)
        cat_result = await session.execute(cat_stmt)
        category = cat_result.scalar_one_or_none()
        category_name = category.category_name if category else "IT Assets"
        
        pr_data = PRCreate(
            title=f"Replacement for Damaged Asset {incident.asset.asset_tag}",
            justification=f"Asset {incident.asset.asset_tag} was damaged and needs replacement. Incident ID: {incident.incident_id}",
            department_id=incident.asset.department_id,
            priority="High",
            purchase_type="Standard",
            items=[
                PRItemCreate(
                    category=category_name,
                    item_name=f"Replacement: {incident.asset.model or incident.asset.asset_tag}",
                    specification="Equivalent or better model",
                    quantity=1,
                    unit_price=Decimal("1000.00") # Dummy estimated price
                )
            ]
        )
        
        new_pr = await pr_service.create_pr(pr_data, current_user.user_id)
        # Optionally, auto submit the PR
        await pr_service.submit_pr(new_pr.pr_id, current_user.user_id)
        
        incident.linked_pr_id = new_pr.pr_id

    elif data.action == "Close":
        incident.status = "Closed"
        incident.resolution = data.resolution

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action {data.action} for status {incident.status}")

    await session.commit()
    await session.refresh(incident)
    return incident
