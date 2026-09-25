import re

with open('src/api/expenses.py', 'r') as f:
    content = f.read()

# 1. Update list_expenses roles
content = content.replace(
    'if "Admin" in role_names or "Finance" in role_names or "Finance Manager" in role_names or "CFO" in role_names:',
    'if "Admin" in role_names or "Finance" in role_names or "Finance Manager" in role_names or "CFO" in role_names or "CEO" in role_names:'
)

# 2. Modify _get_owned_draft to _get_owned_editable_report
old_draft_func = """async def _get_owned_draft(repo: ExpenseRepository, report_id: int, user: User) -> ExpenseReport:
    report = await _get_accessible_report(repo, report_id, user)
    if report.status != "Draft":
        raise HTTPException(status_code=400, detail="Report is not in draft state")
    if report.employee_id != user.user_id:
        _log_action(user, "expense_draft_access_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=404, detail="Expense report not found")
    return report"""

new_draft_func = """async def _get_owned_editable_report(repo: ExpenseRepository, report_id: int, user: User) -> ExpenseReport:
    report = await _get_accessible_report(repo, report_id, user)
    if report.status not in ("Draft", "Returned for Correction"):
        raise HTTPException(status_code=400, detail="Report is not in an editable state")
    if report.employee_id != user.user_id:
        _log_action(user, "expense_draft_access_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=404, detail="Expense report not found")
    return report"""

content = content.replace(old_draft_func, new_draft_func)

# Replace usages
content = content.replace('_get_owned_draft', '_get_owned_editable_report')

# 3. Add justification check to reject_expense
old_reject = """@router.post("/{report_id}/reject")
async def reject_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    from src.models.expense import ExpenseApproval
    from sqlalchemy import select"""

new_reject = """@router.post("/{report_id}/reject")
async def reject_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not payload.comments or not payload.comments.strip():
        raise HTTPException(status_code=400, detail="Justification is required for rejecting a claim")
        
    from src.models.expense import ExpenseApproval
    from sqlalchemy import select"""
content = content.replace(old_reject, new_reject)


# 4. Add justification check to return_expense
old_return = """@router.post("/{report_id}/return")
async def return_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    from src.models.expense import ExpenseApproval
    from sqlalchemy import select"""

new_return = """@router.post("/{report_id}/return")
async def return_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not payload.comments or not payload.comments.strip():
        raise HTTPException(status_code=400, detail="Justification is required for returning a claim")
        
    from src.models.expense import ExpenseApproval
    from sqlalchemy import select"""
content = content.replace(old_return, new_return)

with open('src/api/expenses.py', 'w') as f:
    f.write(content)

print("Done")
