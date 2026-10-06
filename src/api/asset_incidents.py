from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User, Role
from src.models.assets import Asset, AssetIncident, AssetCategory, AssetAssignment, AssetHistory
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
    stmt = select(Asset).options(
        selectinload(Asset.assignments)
    ).where(Asset.asset_id == data.asset_id)
    result = await session.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.assigned_employee_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only report incidents on your assigned assets")

    # Combine description with reason/justification/comments if provided
    full_desc = data.description
    if data.reason:
        full_desc += f"\nReason / Justification: {data.reason}"
    if data.comments:
        full_desc += f"\nComments: {data.comments}"

    incident_status = "Draft" if data.is_draft else "Reported"

    incident = AssetIncident(
        asset_id=data.asset_id,
        reporter_id=current_user.user_id,
        description=full_desc,
        incident_type=data.incident_type,
        incident_date=data.incident_date or date.today(),
        image_url=data.image_url,
        status=incident_status
    )
    
    session.add(incident)
    await session.flush()

    # Record in Asset History
    history = AssetHistory(
        asset_id=asset.asset_id,
        action_type="Incident Reported" if not data.is_draft else "Incident Draft Saved",
        action_by=current_user.user_id,
        details=f"Incident #{incident.incident_id} ({data.incident_type}): {data.description[:100]}"
    )
    session.add(history)

    await session.commit()
    
    # Reload with relationships
    stmt_reload = select(AssetIncident).options(
        selectinload(AssetIncident.asset),
        selectinload(AssetIncident.reporter)
    ).where(AssetIncident.incident_id == incident.incident_id)
    res = await session.execute(stmt_reload)
    return res.scalar_one()

@router.get("", response_model=List[AssetIncidentSchema])
async def list_incidents(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(AssetIncident).options(
        selectinload(AssetIncident.asset),
        selectinload(AssetIncident.reporter)
    ).outerjoin(User, AssetIncident.reporter_id == User.user_id)
    
    conditions = [AssetIncident.reporter_id == current_user.user_id]
    
    user_roles = [r.role_name for r in current_user.roles]
    if "Manager" in user_roles:
        # Managers can see incidents from their direct reports or department
        conditions.append(
            (User.manager_id == current_user.user_id) & (AssetIncident.status != "Draft")
        )
        if current_user.department_id:
            conditions.append(
                (User.department_id == current_user.department_id) & (AssetIncident.status != "Draft")
            )
        
    if any(r in ("Admin", "SuperAdmin", "IT") for r in user_roles):
        # Admins can see all non-drafts or all incidents
        conditions.append(AssetIncident.status != "Draft")
        
    stmt = stmt.where(or_(*conditions)).order_by(AssetIncident.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/{incident_id}", response_model=AssetIncidentSchema)
async def get_incident(
    incident_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(AssetIncident).options(
        selectinload(AssetIncident.asset),
        selectinload(AssetIncident.reporter)
    ).where(AssetIncident.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    user_roles = [r.role_name for r in current_user.roles]
    is_admin = any(r in ("Admin", "SuperAdmin") for r in user_roles)
    is_manager = "Manager" in user_roles
    
    if incident.reporter_id != current_user.user_id and not is_admin and not is_manager:
        raise HTTPException(status_code=403, detail="Not authorized to view this incident")

    return incident

@router.put("/{incident_id}", response_model=AssetIncidentSchema)
async def update_incident(
    incident_id: int,
    data: AssetIncidentUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(AssetIncident).options(
        selectinload(AssetIncident.asset),
        selectinload(AssetIncident.reporter)
    ).where(AssetIncident.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.reporter_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own incidents")

    if incident.status not in ["Draft", "Returned for Correction"]:
        raise HTTPException(status_code=400, detail="Incident can only be edited when Draft or Returned for Correction")

    full_desc = data.description or incident.description
    if data.reason:
        full_desc += f"\nReason / Justification: {data.reason}"
    if data.comments:
        full_desc += f"\nComments: {data.comments}"

    incident.description = full_desc

    if data.incident_type is not None:
        incident.incident_type = data.incident_type
    if data.image_url is not None:
        incident.image_url = data.image_url
    if data.incident_date is not None:
        incident.incident_date = data.incident_date

    # If returned for correction, resubmitting sets it back to Submitted
    was_returned = incident.status == "Returned for Correction"
    if was_returned:
        incident.status = "Submitted"
        history = AssetHistory(
            asset_id=incident.asset_id,
            action_type="Incident Resubmitted",
            action_by=current_user.user_id,
            details=f"Incident #{incident.incident_id} corrected and resubmitted."
        )
        session.add(history)
        
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
    is_admin = any(r in ("Admin", "SuperAdmin") for r in user_roles)
    is_manager = "Manager" in user_roles
    
    stmt = select(AssetIncident).options(
        selectinload(AssetIncident.asset).selectinload(Asset.assignments),
        selectinload(AssetIncident.reporter)
    ).where(AssetIncident.incident_id == incident_id)
    result = await session.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Manager Actions (when status is Submitted)
    if incident.status in ["Submitted", "Reported"]:
        if not is_manager and not is_admin:
            raise HTTPException(status_code=403, detail="Only Managers can perform this action")
            
        # Prevent self approval
        if incident.reporter_id == current_user.user_id and not is_admin:
            raise HTTPException(status_code=403, detail="You cannot approve your own incident report")

        if data.action == "Approve":
            if not data.manager_inspection_assessment:
                raise HTTPException(status_code=400, detail="Manager inspection assessment is required before approval")
            incident.status = "Manager Approved"
            incident.manager_inspection_assessment = data.manager_inspection_assessment
            if data.manager_inspection_comments:
                incident.manager_inspection_comments = data.manager_inspection_comments
                
            history = AssetHistory(
                asset_id=incident.asset_id,
                action_type="Manager Approved",
                action_by=current_user.user_id,
                details=f"Manager Assessment: {data.manager_inspection_assessment}. Comments: {data.manager_inspection_comments or 'None'}"
            )
            session.add(history)
                
        elif data.action == "Reject":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Rejection reason is required")
            incident.status = "Rejected"
            incident.resolution = data.resolution
            
            history = AssetHistory(
                asset_id=incident.asset_id,
                action_type="Manager Rejected",
                action_by=current_user.user_id,
                details=f"Manager Rejection Reason: {data.resolution}"
            )
            session.add(history)
            
        elif data.action == "Return for Correction":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Correction reason is required")
            incident.status = "Returned for Correction"
            incident.resolution = data.resolution
            
            history = AssetHistory(
                asset_id=incident.asset_id,
                action_type="Returned for Correction",
                action_by=current_user.user_id,
                details=f"Manager Return Reason: {data.resolution}"
            )
            session.add(history)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action '{data.action}' for submitted incident")

    # Admin Actions (when status is Manager Approved or Admin Review)
    elif incident.status == "Manager Approved":
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only Administrators can perform Admin incident reviews")
            
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
                if incident.asset:
                    incident.asset.status = "Under Maintenance"
            else:
                incident.status = "Resolved / Completed"
                
            history = AssetHistory(
                asset_id=incident.asset_id,
                action_type="Admin Inspection Resolution",
                action_by=current_user.user_id,
                details=f"Resolution: {data.admin_inspection_resolution}. Notes: {data.admin_comments or 'None'}"
            )
            session.add(history)
                
        elif data.action == "Reject":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Rejection reason is required")
            incident.status = "Rejected"
            incident.resolution = data.resolution
            
            history = AssetHistory(
                asset_id=incident.asset_id,
                action_type="Admin Rejected",
                action_by=current_user.user_id,
                details=f"Admin Rejection Reason: {data.resolution}"
            )
            session.add(history)
            
        elif data.action == "Return for Correction":
            if not data.resolution:
                raise HTTPException(status_code=400, detail="Correction reason is required")
            incident.status = "Returned for Correction"
            incident.resolution = data.resolution
            
            history = AssetHistory(
                asset_id=incident.asset_id,
                action_type="Admin Returned for Correction",
                action_by=current_user.user_id,
                details=f"Admin Return Reason: {data.resolution}"
            )
            session.add(history)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action '{data.action}' for manager-approved incident")

    # Admin Replacement Assignment or Procurement Trigger (when status is Admin Approved)
    elif incident.status == "Admin Approved":
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only Admins can fulfill replacements")
            
        if data.action in ["Assign Replacement", "Replace", "Fulfill Replacement"]:
            available_asset = None
            if data.replacement_asset_id:
                avail_stmt = select(Asset).where(
                    Asset.asset_id == data.replacement_asset_id,
                    Asset.status.in_(["Available", "Unassigned", "In Stock"])
                )
                avail_res = await session.execute(avail_stmt)
                available_asset = avail_res.scalar_one_or_none()
                if not available_asset:
                    raise HTTPException(status_code=400, detail="Selected replacement asset is unavailable or already assigned.")
            else:
                # Auto check inventory for matching available asset in the same category
                if incident.asset and incident.asset.category_id:
                    avail_stmt = select(Asset).where(
                        Asset.status.in_(["Available", "Unassigned", "In Stock"]),
                        Asset.category_id == incident.asset.category_id
                    )
                else:
                    avail_stmt = select(Asset).where(
                        Asset.status.in_(["Available", "Unassigned", "In Stock"])
                    )
                avail_result = await session.execute(avail_stmt)
                available_asset = avail_result.scalars().first()

            old_employee_id = incident.asset.assigned_employee_id or incident.reporter_id

            if available_asset:
                # End old asset assignment
                for assignment in incident.asset.assignments:
                    if assignment.status == "Active":
                        assignment.status = "Returned"
                        assignment.return_date = date.today()
                        assignment.notes = f"Returned due to replacement for Incident #{incident.incident_id}"
                
                incident.asset.assigned_employee_id = None
                incident.asset.status = "Out of Service"
                
                # Assign replacement asset
                available_asset.status = "Assigned"
                available_asset.assigned_employee_id = old_employee_id
                
                new_assignment = AssetAssignment(
                    asset_id=available_asset.asset_id,
                    assigned_to=old_employee_id,
                    assigned_by=current_user.user_id,
                    assigned_date=date.today(),
                    status="Active",
                    notes=f"Replacement for incident #{incident.incident_id} ({incident.asset.asset_tag})"
                )
                session.add(new_assignment)

                # History records
                hist_old = AssetHistory(
                    asset_id=incident.asset.asset_id,
                    action_type="Replaced",
                    action_by=current_user.user_id,
                    details=f"Asset replaced by {available_asset.asset_tag}. Status set to Out of Service."
                )
                session.add(hist_old)

                hist_new = AssetHistory(
                    asset_id=available_asset.asset_id,
                    action_type="Assignment",
                    action_by=current_user.user_id,
                    details=f"Assigned to employee #{old_employee_id} as replacement for Incident #{incident.incident_id}"
                )
                session.add(hist_new)

                incident.status = "Resolved / Completed"
                incident.resolution = f"Replaced with asset {available_asset.asset_tag} ({available_asset.model or 'Asset'})."
            else:
                # Trigger existing procurement workflow
                incident.status = "Waiting for Procurement"
                pr_service = PRService(session)
                
                cat_stmt = select(AssetCategory).where(AssetCategory.category_id == incident.asset.category_id)
                cat_result = await session.execute(cat_stmt)
                category = cat_result.scalar_one_or_none()
                category_name = category.category_name if category else "Hardware"
                
                pr_data = PRCreate(
                    title=f"Replacement for Damaged Asset {incident.asset.asset_tag}",
                    justification=f"Asset {incident.asset.asset_tag} damaged and requires replacement. Incident ID: #{incident.incident_id}. Manager Assessment: {incident.manager_inspection_assessment}. Admin Resolution: {incident.admin_inspection_resolution}.",
                    department_id=incident.asset.department_id,
                    priority="High",
                    purchase_type="Standard",
                    items=[
                        PRItemCreate(
                            category=category_name,
                            item_name=f"Replacement: {incident.asset.model or incident.asset.asset_tag}",
                            specification=f"Equivalent or better replacement for {incident.asset.asset_tag}",
                            quantity=1,
                            unit_price=Decimal("0.00")
                        )
                    ]
                )
                new_pr = await pr_service.create_pr(pr_data, current_user.user_id)
                await pr_service.submit_pr(new_pr.pr_id, current_user.user_id)
                incident.linked_pr_id = new_pr.pr_id

                hist_proc = AssetHistory(
                    asset_id=incident.asset.asset_id,
                    action_type="Procurement Triggered",
                    action_by=current_user.user_id,
                    details=f"No stock available. Triggered procurement PR #{new_pr.pr_number}."
                )
                session.add(hist_proc)
        else:
            raise HTTPException(status_code=400, detail="Invalid action for Admin Approved status")
            
    elif incident.status == "Waiting for Procurement":
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only Admins can complete procurement replacement")
            
        if data.action in ["Complete Procurement Replacement", "Assign Replacement"]:
            avail_stmt = select(Asset).where(
                Asset.status.in_(["Available", "Unassigned", "In Stock"])
            )
            avail_result = await session.execute(avail_stmt)
            available_asset = avail_result.scalars().first()
            
            if available_asset:
                old_employee_id = incident.reporter_id or incident.asset.assigned_employee_id

                for assignment in incident.asset.assignments:
                    if assignment.status == "Active":
                        assignment.status = "Returned"
                        assignment.return_date = date.today()
                incident.asset.assigned_employee_id = None
                incident.asset.status = "Out of Service"

                available_asset.status = "Assigned"
                available_asset.assigned_employee_id = old_employee_id
                
                new_assignment = AssetAssignment(
                    asset_id=available_asset.asset_id,
                    assigned_to=old_employee_id,
                    assigned_by=current_user.user_id,
                    assigned_date=date.today(),
                    status="Active",
                    notes=f"Procured Replacement for incident #{incident.incident_id}"
                )
                session.add(new_assignment)
                
                hist_proc_done = AssetHistory(
                    asset_id=available_asset.asset_id,
                    action_type="Assignment",
                    action_by=current_user.user_id,
                    details=f"Procured replacement assigned to employee #{old_employee_id} for Incident #{incident.incident_id}"
                )
                session.add(hist_proc_done)

                incident.status = "Resolved / Completed"
                incident.resolution = f"Procured and replaced with asset {available_asset.asset_tag}."
            else:
                raise HTTPException(status_code=400, detail="No available asset in stock yet. Complete GRN inspection first.")
                
    elif incident.status == "Repair":
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only Admins can manage repair status")
        
        if data.action in ["Complete Repair", "Repair Completed"]:
            incident.status = "Resolved / Completed"
            incident.resolution = data.resolution or "Repair completed successfully and asset restored to service."
            incident.asset.status = "Assigned"
            
            hist_repair = AssetHistory(
                asset_id=incident.asset.asset_id,
                action_type="Repair Completed",
                action_by=current_user.user_id,
                details=f"Asset repair completed. {data.admin_comments or ''}"
            )
            session.add(hist_repair)

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action '{data.action}' for status '{incident.status}'")

    await session.commit()
    
    # Reload with full relationships
    stmt_reload = select(AssetIncident).options(
        selectinload(AssetIncident.asset),
        selectinload(AssetIncident.reporter)
    ).where(AssetIncident.incident_id == incident.incident_id)
    res = await session.execute(stmt_reload)
    return res.scalar_one()

