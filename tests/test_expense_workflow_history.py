import pytest
from src.models.approval import ApprovalWorkflow
from src.models.expense import ExpenseReport
from src.database.base import Base
from sqlalchemy.orm import selectinload
from sqlalchemy import select

@pytest.mark.asyncio
async def test_expense_report_workflow_history_isolation(db_session, setup_test_users):
    user_id = setup_test_users["employee"].user_id
    
    # 1. Create an ExpenseReport
    report = ExpenseReport(employee_id=user_id, purpose="Business Trip", justification="Client Meeting")
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)
    
    # 2. Create an ApprovalWorkflow for this claim
    claim_workflow = ApprovalWorkflow(claim_id=report.expense_report_id, status="Under Review")
    db_session.add(claim_workflow)
    
    # 3. Create an unrelated ApprovalWorkflow for a PR
    pr_workflow = ApprovalWorkflow(pr_id=999, status="Approved")
    db_session.add(pr_workflow)
    
    await db_session.commit()
    
    # 4. Fetch the ExpenseReport with its workflow_history
    stmt = select(ExpenseReport).where(ExpenseReport.expense_report_id == report.expense_report_id).options(selectinload(ExpenseReport.workflow_history))
    result = await db_session.execute(stmt)
    fetched_report = result.scalar_one()
    
    # 5. Verify it ONLY returns the claim workflow
    assert len(fetched_report.workflow_history) == 1
    assert fetched_report.workflow_history[0].claim_id == report.expense_report_id
    assert fetched_report.workflow_history[0].pr_id is None

