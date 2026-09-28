import pytest
from src.models.approval import ApprovalWorkflow
from src.models.purchase_requisition import PurchaseRequisition
from sqlalchemy.orm import selectinload
from sqlalchemy import select

@pytest.mark.asyncio
async def test_pr_workflow_history_isolation(db_session, setup_test_users):
    user_id = setup_test_users["employee"].user_id
    
    # 1. Create a PR
    pr = PurchaseRequisition(requestor_id=user_id, pr_number="PR-TEST-123", justification="Test", total_estimated_amount=100)
    db_session.add(pr)
    await db_session.commit()
    await db_session.refresh(pr)
    
    # 2. Create an ApprovalWorkflow for this PR
    pr_workflow = ApprovalWorkflow(pr_id=pr.pr_id, status="Under Review")
    db_session.add(pr_workflow)
    
    # 3. Create an unrelated ApprovalWorkflow for an ExpenseClaim
    claim_workflow = ApprovalWorkflow(claim_id=999, status="Approved")
    db_session.add(claim_workflow)
    
    await db_session.commit()
    
    # 4. Fetch the PR with its workflows
    stmt = select(PurchaseRequisition).where(PurchaseRequisition.pr_id == pr.pr_id).options(selectinload(PurchaseRequisition.workflows))
    result = await db_session.execute(stmt)
    fetched_pr = result.scalar_one()
    
    # 5. Verify it ONLY returns the PR workflow
    assert len(fetched_pr.workflows) == 1
    assert fetched_pr.workflows[0].pr_id == pr.pr_id
    assert fetched_pr.workflows[0].claim_id is None

