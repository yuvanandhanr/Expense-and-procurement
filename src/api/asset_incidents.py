from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date
from decimal import Decimal

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User, Role
from src.models.assets import Asset, AssetIncident, AssetCategory, AssetAssignment
from src.schemas.assets import AssetIncidentCreate, AssetIncidentAction, AssetIncidentSchema, AssetIncidentUpdate
from src.services.pr_service import PRService
from src.schemas.purchase_requisition import PRCreate, PRItemCreate

router = APIRouter(prefix="/asset-incidents", tags=["Asset Incidents"])

@router.post("", response_model=AssetIncidentSchema, status_code=status.HTTP_201_CREATED)
async def report_incident(
    data: AssetIncidentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if data.department_name != current_user.department_name or data.employee_type != current_user.employee_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid department or employee type. Please use the values assigned to your employee profile."
        )

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
        image_url=data.image_url,
        status="Draft" if data.is_draft else "Submitted"
    )
    
    session.add(incident)
    await session.commit()
    await session.refresh(incident)
    return incident

@router.get("", response_model=List[AssetIncidentSchema])
async def list_incidents(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(AssetIncident).outerjoin(User, AssetIncident.reporter_id == User.user_id)
    
    conditions = [AssetIncident.reporter_id == current_user.user_id]
    
    user_roles = [r.role_name for r in current_user.roles]
    if "Manager" in user_roles:
        # Managers can see incidents from their reports that are not drafts
        conditions.append(
            (User.manager_id == current_user.user_id) & (AssetIncident.status != "Draft")
        )
        
    if "Admin" in user_roles:
        # Admins can see Manager Approved, Admin Approved, Repair/Replacement, etc.
        conditions.append(AssetIncident.status.in_([
            "Manager Approved", "Admin Approved", "Repair", "Replacement", "Waiting for Procurement", "Replacement Assigned", "Resolved / Completed", "Rejected", "Returned for Correction"
        ]))
        
    stmt = stmt.where(or_(*conditions)).order_by(AssetIncident.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()

@router.put("/{incident_id}", response_model=AssetIncidentSchema)
async def update_incident(
    incident_id: int,
    data: AssetIncidentUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(AssetIncident).where(AssetIncident.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.reporter_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own incidents")

    if incident.status not in ["Draft", "Returned for Correction"]:
        raise HTTPException(status_code=400, detail="Incident can only be edited when Draft or Returned for Correction")

    if data.description is not None:
        incident.description = data.description
    if data.incident_type is not None:
        incident.incident_type = data.incident_type
    if data.image_url is not None:
        incident.image_url = data.image_url

    if incident.status == "Returned for Correction":
        incident.status = "Submitted"
        
    await session.commit()
    await session.refresh(incident)
    return incident

@router.post("/{incident_id}/action", response_model=AssetIncidentSchema)
async def action_incident(
    incident_id: int,
    data: AssetIncidentAction,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    user_roles = [r.role_name for r in current_user.roles]
    
    stmt = select(AssetIncident).options(
        selectinload(AssetIncident.asset).selectinload(Asset.assignments)
    ).where(AssetIncident.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Manager Actions
    if incident.status == "Submitted":
        if "Manager" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Managers can perform this action")
            
        if data.action == "Approve":
            if not data.manager_inspection_assessment:
                raise HTTPException(status_code=400, detail="Manager inspection assessment is required")
            incident.status = "Manager Approved"
            incident.manager_inspection_assessment = data.manager_inspection_assessment
            if data.manager_inspection_comments:
                incident.manager_inspection_comments = data.manager_inspection_comments
                
        elif data.action == "Reject":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Rejection reason is required")
            incident.status = "Rejected"
            incident.resolution = data.resolution
            
        elif data.action == "Return for Correction":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Correction reason is required")
            incident.status = "Returned for Correction"
            incident.resolution = data.resolution
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    # Admin Actions
    elif incident.status == "Manager Approved":
        if "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Admins can perform this action")
            
        if data.action == "Approve":
            if not data.admin_inspection_resolution:
                raise HTTPException(status_code=400, detail="Admin inspection resolution is required")
            
            incident.admin_inspection_resolution = data.admin_inspection_resolution
            if data.admin_comments:
                incident.admin_comments = data.admin_comments
                
            if data.admin_inspection_resolution == "Replacement Required":
                incident.status = "Admin Approved"
            elif data.admin_inspection_resolution == "Repair Required":
                incident.status = "Repair"
            else:
                incident.status = "Resolved / Completed"
                
        elif data.action == "Reject":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Rejection reason is required")
            incident.status = "Rejected"
            incident.resolution = data.resolution
            
        elif data.action == "Return for Correction":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Correction reason is required")
            incident.status = "Returned for Correction"
            incident.resolution = data.resolution
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    elif incident.status == "Admin Approved":
        # Handle replacement workflow
        if "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Admins can perform this action")
            
        if data.action == "Assign Replacement":
            # Check inventory for replacement
            avail_stmt = select(Asset).where(
                Asset.status.in_(["Available", "Unassigned"]),
                Asset.category_id == incident.asset.category_id
            )
            avail_result = await session.execute(avail_stmt)
            available_asset = avail_result.scalars().first()
            
            # End old assignment
            for assignment in incident.asset.assignments:
                if assignment.status == "Active":
                    assignment.status = "Returned"
                    assignment.return_date = date.today()
            
            old_employee_id = incident.asset.assigned_employee_id
            incident.asset.assigned_employee_id = None
            incident.asset.status = "Disposed" # or Out of Service
            
            if available_asset:
                available_asset.status = "Assigned"
                available_asset.assigned_employee_id = old_employee_id
                
                new_assignment = AssetAssignment(
                    asset_id=available_asset.asset_id,
                    assigned_to=old_employee_id,
                    assigned_by=current_user.user_id,
                    assigned_date=date.today(),
                    status="Active",
                    notes=f"Replacement for incident #{incident.incident_id}"
                )
                session.add(new_assignment)
                incident.status = "Resolved / Completed"
            else:
                # Trigger procurement
                incident.status = "Waiting for Procurement"
                pr_service = PRService(session)
                
                cat_stmt = select(AssetCategory).where(AssetCategory.category_id == incident.asset.category_id)
                cat_result = await session.execute(cat_stmt)
                category = cat_result.scalar_one_or_none()
                category_name = category.category_name if category else "Hardware"
                
                pr_data = PRCreate(
                    title=f"Replacement for Damaged Asset {incident.asset.asset_tag}",
                    justification=f"Asset {incident.asset.asset_tag} requires replacement. Incident ID: {incident.incident_id}",
                    department_id=incident.asset.department_id,
                    priority="High",
                    purchase_type="Standard",
                    items=[
                        PRItemCreate(
                            category=category_name,
                            item_name=f"Replacement: {incident.asset.model or incident.asset.asset_tag}",
                            specification="Equivalent or better",
                            quantity=1,
                            unit_price=Decimal("0.00")
                        )
                    ]
                )
                new_pr = await pr_service.create_pr(pr_data, current_user.user_id)
                await pr_service.submit_pr(new_pr.pr_id, current_user.user_id)
                incident.linked_pr_id = new_pr.pr_id
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
    elif incident.status == "Waiting for Procurement":
        if "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Admins can perform this action")
            
        if data.action == "Complete Procurement Replacement":
            avail_stmt = select(Asset).where(
                Asset.status.in_(["Available", "Unassigned"]),
                Asset.category_id == incident.asset.category_id
            )
            avail_result = await session.execute(avail_stmt)
            available_asset = avail_result.scalars().first()
            
            if available_asset:
                available_asset.status = "Assigned"
                available_asset.assigned_employee_id = incident.reporter_id
                
                new_assignment = AssetAssignment(
                    asset_id=available_asset.asset_id,
                    assigned_to=incident.reporter_id,
                    assigned_by=current_user.user_id,
                    assigned_date=date.today(),
                    status="Active",
                    notes=f"Procured Replacement for incident #{incident.incident_id}"
                )
                session.add(new_assignment)
                incident.status = "Resolved / Completed"
            else:
                raise HTTPException(status_code=400, detail="No available asset in stock yet.")
                
    elif incident.status == "Repair":
        if "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Admins can perform this action")
        
        if data.action == "Complete Repair":
            incident.status = "Resolved / Completed"
            incident.asset.status = "Assigned"

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action for status {incident.status}")

    await session.commit()
    await session.refresh(incident)
    return incident
