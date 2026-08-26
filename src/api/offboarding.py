from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user, RoleChecker
from src.models.auth import User
from src.models.assets import Asset, AssetAssignment, AssetHistory, AssetIncident
from src.models.offboarding import OffboardingTask
from src.schemas.offboarding import OffboardingTaskSchema, OffboardingTaskClear

router = APIRouter(prefix="/offboarding", tags=["Offboarding"])

@router.post("/{employee_id}/trigger", response_model=List[OffboardingTaskSchema], status_code=status.HTTP_201_CREATED)
async def trigger_offboarding(
    employee_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(RoleChecker(["Admin", "SuperAdmin", "Manager"]))
):
    # Verify employee
    emp = await session.get(User, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Find active asset assignments
    stmt = select(AssetAssignment).where(
        AssetAssignment.assigned_to == employee_id,
        AssetAssignment.status == "Active"
    )
    result = await session.execute(stmt)
    assignments = result.scalars().all()

    tasks = []
    
    # Manager Approval task
    mgr_task = OffboardingTask(
        employee_id=employee_id,
        task_type="Manager Approval",
        notes=f"Approve offboarding for {emp.first_name}"
    )
    session.add(mgr_task)
    tasks.append(mgr_task)

    # Create Retrieve Asset tasks
    for assignment in assignments:
        task = OffboardingTask(
            employee_id=employee_id,
            asset_id=assignment.asset_id,
            task_type="Retrieve Asset",
            notes=f"Retrieve asset {assignment.asset_id} from {emp.first_name}"
        )
        session.add(task)
        tasks.append(task)
        
    # Create generic Revoke IT Access task
    it_task = OffboardingTask(
        employee_id=employee_id,
        task_type="Revoke IT Access",
        notes=f"Revoke all system access for {emp.first_name}"
    )
    session.add(it_task)
    tasks.append(it_task)
    
    # Create Financial Clearance task
    fin_task = OffboardingTask(
        employee_id=employee_id,
        task_type="Financial Clearance",
        notes=f"Clear pending dues for {emp.first_name}"
    )
    session.add(fin_task)
    tasks.append(fin_task)
    
    await session.commit()
    for task in tasks:
        await session.refresh(task)
        
    return tasks

@router.post("/tasks/{task_id}/clear", response_model=OffboardingTaskSchema)
async def clear_offboarding_task(
    task_id: int,
    data: OffboardingTaskClear,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(RoleChecker(["Admin", "SuperAdmin", "IT", "Finance", "Manager"]))
):
    task = await session.get(OffboardingTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status in ["Cleared", "Rejected", "Blocked"]:
        raise HTTPException(status_code=400, detail="Task is already processed")

    if data.action == "Reject" and task.task_type == "Manager Approval":
        task.status = "Rejected"
        task.cleared_by = current_user.user_id
        task.cleared_at = datetime.utcnow()
        if data.notes:
            task.notes = f"{task.notes}\nRejected notes: {data.notes}"
        await session.commit()
        await session.refresh(task)
        return task

    if data.action == "Pending Dues" and task.task_type == "Financial Clearance":
        task.status = "Blocked"
        task.cleared_by = current_user.user_id
        task.cleared_at = datetime.utcnow()
        if data.notes:
            task.notes = f"{task.notes}\nBlocked due to pending dues: {data.notes}"
        await session.commit()
        await session.refresh(task)
        return task
        
    task.status = "Cleared"
    task.cleared_by = current_user.user_id
    task.cleared_at = datetime.utcnow()
    if data.notes:
        task.notes = f"{task.notes}\nClearance notes: {data.notes}"

    if task.task_type == "Retrieve Asset" and task.asset_id:
        # Mark assignment as returned
        stmt = select(AssetAssignment).where(
            AssetAssignment.asset_id == task.asset_id,
            AssetAssignment.assigned_to == task.employee_id,
            AssetAssignment.status == "Active"
        )
        result = await session.execute(stmt)
        assignment = result.scalar_one_or_none()
        
        if assignment:
            assignment.status = "Returned"
            assignment.return_date = datetime.today().date()
            
            # Update asset status
            asset = await session.get(Asset, task.asset_id)
            if asset:
                if data.asset_condition == "Damaged":
                    asset.status = "Damaged"
                    incident = AssetIncident(
                        asset_id=asset.asset_id,
                        reporter_id=current_user.user_id,
                        description=f"Damaged upon offboarding return: {data.notes or 'No notes'}",
                        incident_type="Damage",
                        status="Reported"
                    )
                    session.add(incident)
                elif data.asset_condition == "Lost":
                    asset.status = "Lost"
                else:
                    asset.status = "Available"
                asset.assigned_employee_id = None
                
                # History
                history = AssetHistory(
                    asset_id=asset.asset_id,
                    action_type="Return",
                    action_by=current_user.user_id,
                    details=f"Returned during offboarding. Task {task.task_id}. Condition: {data.asset_condition or 'Good'}"
                )
                session.add(history)
                
    await session.commit()
    await session.refresh(task)
    return task

@router.post("/{employee_id}/finalize")
async def finalize_offboarding(
    employee_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(RoleChecker(["Admin", "SuperAdmin"]))
):
    # Check if all tasks are cleared
    stmt = select(OffboardingTask).where(
        OffboardingTask.employee_id == employee_id,
        OffboardingTask.status.in_(["Pending", "Blocked", "Rejected"])
    )
    result = await session.execute(stmt)
    pending_tasks = result.scalars().all()
    
    if pending_tasks:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot finalize. {len(pending_tasks)} tasks are pending, blocked or rejected."
        )
        
    emp = await session.get(User, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    emp.status = "Inactive"
    await session.commit()
    
    return {"message": "Offboarding finalized successfully. Employee is now inactive."}
