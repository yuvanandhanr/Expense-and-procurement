import pytest
from sqlalchemy.exc import IntegrityError
from src.models.approval import ApprovalWorkflow
from src.database.base import Base
from sqlalchemy import select

@pytest.mark.asyncio
async def test_workflow_exclusive_ownership(db_session):
    # Test valid: only one ID is set (e.g. pr_id)
    valid_wf1 = ApprovalWorkflow(pr_id=1, status="Under Review")
    db_session.add(valid_wf1)
    await db_session.commit()
    assert valid_wf1.workflow_id is not None
    
    # Test valid: only claim_id
    valid_wf2 = ApprovalWorkflow(claim_id=1, status="Under Review")
    db_session.add(valid_wf2)
    await db_session.commit()
    assert valid_wf2.workflow_id is not None
    
    # Test valid: only po_id
    valid_wf3 = ApprovalWorkflow(po_id=1, status="Under Review")
    db_session.add(valid_wf3)
    await db_session.commit()
    assert valid_wf3.workflow_id is not None
    
    # Test valid: only invoice_id
    valid_wf4 = ApprovalWorkflow(invoice_id=1, status="Under Review")
    db_session.add(valid_wf4)
    await db_session.commit()
    assert valid_wf4.workflow_id is not None

    # Test invalid: all NULL
    invalid_wf_all_null = ApprovalWorkflow(status="Under Review")
    db_session.add(invalid_wf_all_null)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    # Test invalid: multiple set
    invalid_wf_multiple = ApprovalWorkflow(claim_id=1, pr_id=1, status="Under Review")
    db_session.add(invalid_wf_multiple)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

