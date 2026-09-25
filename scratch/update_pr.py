import re

with open("src/api/purchase_requisitions.py", "r") as f:
    content = f.read()

# Update check_pr_access signature
content = content.replace("def check_pr_access(pr, current_user: User) -> None:", "async def check_pr_access(pr, current_user: User, db: AsyncSession) -> None:")

# Update the logic inside check_pr_access
old_logic = """    # Check full access roles
    user_roles = [role.role_name for role in current_user.roles]
    if any(role in user_roles for role in ["Admin", "CFO", "Finance Manager", "Finance", "Manager", "CEO"]):
        return

    # Check Procurement role
    if "Procurement" in user_roles:
        if pr.status in ("Approved", "Assigned to Procurement", "Procurement In Progress", "Completed"):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Procurement can only access fully approved requisitions."
        )

    # Check Manager role
    if "Manager" in user_roles and current_user.department_id:
        if pr.department_id == current_user.department_id:
            return

    # Fallback to Requestor check
    if pr.requestor_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are restricted to accessing your own requisitions only"
        )"""

new_logic = """    if pr.requestor_id == current_user.user_id:
        return
        
    user_roles = [role.role_name for role in current_user.roles]
    
    if "Manager" in user_roles:
        if getattr(pr.requestor, "manager_id", None) == current_user.user_id:
            return

    if "Procurement" in user_roles:
        if pr.status in ("Approved", "Assigned to Procurement", "Procurement In Progress", "Completed"):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Procurement can only access fully approved requisitions."
        )

    from src.models.approval import ApprovalWorkflow, ApprovalStep, ApprovalHistory
    from sqlalchemy import select
    
    wf_query = select(ApprovalWorkflow.workflow_id).where(ApprovalWorkflow.pr_id == pr.pr_id)
    wf_res = await db.execute(wf_query)
    wf_id = wf_res.scalar_one_or_none()
    
    if wf_id:
        step_query = select(ApprovalStep).where(
            ApprovalStep.workflow_id == wf_id,
            (ApprovalStep.approver_id == current_user.user_id) | 
            (ApprovalStep.approver_id.is_(None) & ApprovalStep.approver_role_id.in_([r.role_id for r in current_user.roles]))
        )
        step_res = await db.execute(step_query)
        if step_res.scalars().first():
            return
            
        hist_query = select(ApprovalHistory).join(ApprovalStep, ApprovalHistory.step_id == ApprovalStep.step_id).where(
            ApprovalStep.workflow_id == wf_id,
            ApprovalHistory.performed_by == current_user.user_id
        )
        hist_res = await db.execute(hist_query)
        if hist_res.scalars().first():
            return
            
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to view this requisition."
    )"""

content = content.replace(old_logic, new_logic)

# Replace all calls
content = re.sub(r'check_pr_access\(pr,\s*current_user\)', r'await check_pr_access(pr, current_user, db)', content)

# Also update list_prs
old_list = """async def list_prs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    prs = await service.pr_repo.list_by_requestor(current_user.user_id)
        
    return [pr for pr in prs if not (pr.status == "Draft" and pr.requestor_id != current_user.user_id)]"""

new_list = """async def list_prs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = PRService(db)
    prs = await service.pr_repo.list_accessible_prs(current_user)
        
    return [pr for pr in prs if not (pr.status == "Draft" and pr.requestor_id != current_user.user_id)]"""

content = content.replace(old_list, new_list)

with open("src/api/purchase_requisitions.py", "w") as f:
    f.write(content)

