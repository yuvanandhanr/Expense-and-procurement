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
        image_url=data.image_url,
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
    from sqlalchemy import select, or_
    from src.models.auth import User as UserModel, Role
    
    stmt = select(AssetIncident).outerjoin(UserModel, AssetIncident.reporter_id == UserModel.user_id)
    
    conditions = [AssetIncident.reporter_id == current_user.user_id]
    
    user_roles = [r.role_name for r in current_user.roles]
    if "Manager" in user_roles:
        manager_cond1 = (UserModel.manager_id == current_user.user_id) & (AssetIncident.status != "Draft")
        manager_cond2 = (AssetIncident.status == "Reported") & (UserModel.manager_id == current_user.user_id)
        
        if not any(r in user_roles for r in ["Admin", "SuperAdmin", "CEO", "CFO"]):
            manager_cond1 = manager_cond1 & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
            manager_cond2 = manager_cond2 & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
            
        conditions.append(manager_cond1)
        conditions.append(manager_cond2)
        
    if "Admin" in user_roles or "IT" in user_roles:
        conditions.append(AssetIncident.status == "Pending Fulfillment")
        
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

    if incident.status != "Returned for Correction":
        raise HTTPException(status_code=400, detail="Incident can only be edited when returned for correction")

    if data.description is not None:
        incident.description = data.description
    if data.incident_type is not None:
        incident.incident_type = data.incident_type
    if data.image_url is not None:
        incident.image_url = data.image_url

    # Re-submit for approval
    incident.status = "Reported"

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

    if data.action == "Approve" and incident.status == "Reported":
        if "Manager" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Managers can approve incidents")
        if not data.physical_inspection_done:
            raise HTTPException(status_code=400, detail="Physical inspection is mandatory before approval")
            
        incident.status = "Pending Fulfillment"
        incident.resolution = data.resolution
        incident.physical_inspection_done = data.physical_inspection_done

    elif data.action == "Reject" and incident.status == "Reported":
        if "Manager" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Managers can reject reports")
        incident.status = "Rejected"
        incident.resolution = data.resolution
        incident.asset.status = "Assigned" # Revert asset status

    elif data.action == "Return for Correction" and incident.status in ["Reported", "Pending Fulfillment", "Approved"]:
        if "Manager" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only Managers can return reports")
        incident.status = "Returned for Correction"
        incident.resolution = data.resolution

    elif data.action == "Repair" and incident.status == "Pending Fulfillment":
        if "IT" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only IT/Admin can log repairs")
            
        incident.status = "Repair"
        incident.resolution = data.resolution
        incident.asset.status = "Under Maintenance"

    elif data.action == "Replace" and incident.status == "Pending Fulfillment":
        if "IT" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only IT/Admin can log replacements")
            
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

        # Check if replacement asset is available in stock
        avail_stmt = select(Asset).where(
            Asset.status == "Available",
            Asset.category_id == incident.asset.category_id
        )
        avail_result = await session.execute(avail_stmt)
        available_asset = avail_result.scalars().first()

        if available_asset:
            # Issue from stock
            incident.status = "Replacement Assigned"
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
        else:
            # Automatically create PR for replacement
            incident.status = "Waiting for Procurement"
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

    elif data.action == "Assign Replacement" and incident.status == "Waiting for Procurement":
        if "IT" not in user_roles and "Admin" not in user_roles:
            raise HTTPException(status_code=403, detail="Only IT/Admin can assign replacement assets")

        # Check if replacement asset has arrived in stock
        avail_stmt = select(Asset).where(
            Asset.status == "Available",
            Asset.category_id == incident.asset.category_id
        )
        avail_result = await session.execute(avail_stmt)
        available_asset = avail_result.scalars().first()

        if available_asset:
            # Issue from stock
            incident.status = "Replacement Assigned"
            available_asset.status = "Assigned"
            available_asset.assigned_employee_id = incident.reporter_id
            
            from src.models.assets import AssetAssignment
            from datetime import date
            new_assignment = AssetAssignment(
                asset_id=available_asset.asset_id,
                assigned_to=incident.reporter_id,
                assigned_by=current_user.user_id,
                assigned_date=date.today(),
                status="Active",
                notes=f"Replacement for incident #{incident.incident_id}"
            )
            session.add(new_assignment)
            if data.resolution:
                incident.resolution = data.resolution
        else:
            raise HTTPException(status_code=400, detail="No available replacement asset found in stock yet. Please wait for procurement to complete.")

    elif data.action == "Close":
        incident.status = "Closed"
        incident.resolution = data.resolution

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action {data.action} for status {incident.status}")

    await session.commit()
    await session.refresh(incident)
    
    # Send notification to the employee who reported it
    try:
        from src.services.notification_service import NotificationService
        notif_service = NotificationService(session)
        await notif_service.send_notification(
            user_id=incident.reporter_id,
            template_name="AssetIncidentUpdateAlert",
            context={
                "asset_name": incident.asset.asset_name,
                "status": incident.status,
                "resolution": incident.resolution or "No notes provided"
            }
        )
    except Exception:
        pass
        
    return incident
