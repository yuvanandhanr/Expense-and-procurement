import pytest
from src.api.expenses import approve_expense
from src.models.expense import ExpenseReport, ExpenseApproval
from src.schemas.expense import ExpenseActionPayload
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_expense_approval_wildcard_removal(db_session, setup_test_users):
    user_id = setup_test_users["manager"].user_id
    
    # 1. Create ExpenseReport
    report = ExpenseReport(
        employee_id=setup_test_users["employee"].user_id,
        purpose="Test Purpose",
        justification="Test Justification",
        status="Pending Manager Approval"
    )
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)
    
    # 2. Create Pending step assigned to NO ONE
    approval = ExpenseApproval(expense_report_id=report.expense_report_id, status="Pending", approver_id=None)
    db_session.add(approval)
    await db_session.commit()
    
    # 3. Try to approve it as the manager
    payload = ExpenseActionPayload(comments="Approve wildcard")
    with pytest.raises(HTTPException) as exc:
        await approve_expense(report.expense_report_id, payload, db_session, setup_test_users["manager"])
        
    assert exc.value.status_code == 403
    assert "No matching pending approval step found" in exc.value.detail
    
    # 4. Now assign it explicitly to the manager
    approval.approver_id = user_id
    await db_session.commit()
    
    # 5. Approve should succeed
    res = await approve_expense(report.expense_report_id, payload, db_session, setup_test_users["manager"])
    assert res["status"] == "Approved"

