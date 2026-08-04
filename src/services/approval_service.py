from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.auth import User, Role
from src.models.purchase_requisition import PurchaseRequisition
from src.models.approval import (
    ApprovalMatrix,
    ApprovalWorkflow,
    ApprovalStep,
    WorkflowHistory,
    ApprovalHistory,
    ApprovalComment,
)
from src.repositories.purchase_requisition import PRRepository
from src.repositories.approval import (
    ApprovalWorkflowRepository,
    ApprovalStepRepository,
    WorkflowHistoryRepository,
    ApprovalHistoryRepository,
    CommentRepository,
)
from src.services.budget_service import BudgetService


class ApprovalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pr_repo = PRRepository(db)
        self.workflow_repo = ApprovalWorkflowRepository(db)
        self.step_repo = ApprovalStepRepository(db)
        self.workflow_history_repo = WorkflowHistoryRepository(db)
        self.approval_history_repo = ApprovalHistoryRepository(db)
        self.comment_repo = CommentRepository(db)
        self.budget_service = BudgetService(db)

    async def get_cfo_role_id(self) -> int:
        """
        Locates the CFO role or returns Admin (role_id=4) as fallback.
        """
        query = select(Role).where(Role.role_name == "CFO")
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        return role.role_id if role else 4

    async def generate_workflow(self, pr: PurchaseRequisition) -> ApprovalWorkflow:
        """
        Evaluates approval matrix rules and builds step routing chain.
        """
        # Fetch matching rules from matrix
        from src.models.approval import ApprovalMatrix
        query = (
            select(ApprovalMatrix)
            .where(
                ApprovalMatrix.min_amount <= pr.total_estimated_amount,
                ApprovalMatrix.max_amount >= pr.total_estimated_amount
            )
            .order_by(ApprovalMatrix.approval_level.asc())
        )
        result = await self.db.execute(query)
        rules = list(result.scalars().all())

        steps_to_create = []
        
        # If rules exist, parse them. Otherwise generate default Manager -> Finance steps.
        if rules:
            for idx, rule in enumerate(rules, start=1):
                steps_to_create.append({
                    "step_number": idx,
                    "approver_role_id": rule.role_id,
                    "approver_id": None
                })
        else:
            # Default fallback: Level 1 Manager, Level 2 Finance
            steps_to_create.append({"step_number": 1, "approver_role_id": 2, "approver_id": None}) # Manager
            steps_to_create.append({"step_number": 2, "approver_role_id": 3, "approver_id": None}) # Finance

        # High-value threshold check (> $50,000 automatically requires CFO approval)
        if pr.total_estimated_amount > Decimal("50000.00"):
            cfo_role_id = await self.get_cfo_role_id()
            # Check if CFO role step is already present
            cfo_exists = any(s["approver_role_id"] == cfo_role_id for s in steps_to_create)
            if not cfo_exists:
                steps_to_create.append({
                    "step_number": len(steps_to_create) + 1,
                    "approver_role_id": cfo_role_id,
                    "approver_id": None
                })

        # Create overall workflow
        workflow = ApprovalWorkflow(
            pr_id=pr.pr_id,
            status="Under Review",
            created_at=datetime.utcnow()
        )
        workflow = await self.workflow_repo.create(workflow)

        # Create step records
        for s in steps_to_create:
            step = ApprovalStep(
                workflow_id=workflow.workflow_id,
                step_number=s["step_number"],
                approver_role_id=s["approver_role_id"],
                approver_id=s["approver_id"],
                status="Pending"
            )
            await self.step_repo.create(step)

        # Update initial PR status
        first_step_role_id = steps_to_create[0]["approver_role_id"]
        pr.status = self._get_status_from_role_id(first_step_role_id)
        await self.pr_repo.update(pr)

        # Log to workflow history
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Submitted",
            performed_by=pr.requestor_id,
            from_status="Draft",
            to_status=pr.status,
            comments="Purchase Requisition submitted for approval",
            created_at=datetime.utcnow()
        )
        await self.workflow_history_repo.create(w_hist)

        return workflow

    async def get_active_step(self, pr_id: int) -> ApprovalStep:
        workflow = await self.workflow_repo.get_by_pr_id(pr_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval workflow not found for this requisition"
            )
        active_step = await self.step_repo.get_active_step_for_workflow(workflow.workflow_id)
        if not active_step:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending approval steps found in this workflow"
            )
        return active_step

    async def approve_step(self, pr_id: int, user_id: int, comments: Optional[str] = None) -> PurchaseRequisition:
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        active_step = await self.get_active_step(pr_id)

        # Update active step
        active_step.status = "Approved"
        active_step.approver_id = user_id
        active_step.actioned_at = datetime.utcnow()
        await self.step_repo.update(active_step)

        # Log approval history
        app_hist = ApprovalHistory(
            step_id=active_step.step_id,
            action="Approve",
            performed_by=user_id,
            comments=comments or "Approved",
            created_at=datetime.utcnow()
        )
        await self.approval_history_repo.create(app_hist)

        # Find next step
        workflow = await self.workflow_repo.get_by_pr_id(pr_id)
        next_step = await self.step_repo.get_active_step_for_workflow(workflow.workflow_id)

        old_status = pr.status

        if next_step:
            # Advance to next step role status
            pr.status = self._get_status_from_role_id(next_step.approver_role_id)
            await self.pr_repo.update(pr)
            
            w_hist = WorkflowHistory(
                pr_id=pr.pr_id,
                action="Under Review",
                performed_by=user_id,
                from_status=old_status,
                to_status=pr.status,
                comments=f"Step approved. Routing to level {next_step.step_number}",
                created_at=datetime.utcnow()
            )
            await self.workflow_history_repo.create(w_hist)
        else:
            # Workflow completed successfully
            workflow.status = "Approved"
            await self.workflow_repo.update(workflow)

            # Perform final budget commit
            if pr.budget_code:
                await self.budget_service.commit_budget(pr.pr_id)

            pr.status = "Approved"
            await self.pr_repo.update(pr)

            w_hist = WorkflowHistory(
                pr_id=pr.pr_id,
                action="Approved",
                performed_by=user_id,
                from_status=old_status,
                to_status="Approved",
                comments="PR approved successfully by final authority",
                created_at=datetime.utcnow()
            )
            await self.workflow_history_repo.create(w_hist)

        return pr

    async def reject_step(self, pr_id: int, user_id: int, comments: str) -> PurchaseRequisition:
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        active_step = await self.get_active_step(pr_id)

        # Reject step
        active_step.status = "Rejected"
        active_step.approver_id = user_id
        active_step.actioned_at = datetime.utcnow()
        await self.step_repo.update(active_step)

        # Reject workflow
        workflow = await self.workflow_repo.get_by_pr_id(pr_id)
        workflow.status = "Rejected"
        await self.workflow_repo.update(workflow)

        # Release budget reservation
        if pr.budget_code:
            await self.budget_service.release_budget(pr.pr_id)

        old_status = pr.status
        pr.status = "Rejected"
        await self.pr_repo.update(pr)

        # Log approval history
        app_hist = ApprovalHistory(
            step_id=active_step.step_id,
            action="Reject",
            performed_by=user_id,
            comments=comments,
            created_at=datetime.utcnow()
        )
        await self.approval_history_repo.create(app_hist)

        # Log workflow history
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Rejected",
            performed_by=user_id,
            from_status=old_status,
            to_status="Rejected",
            comments=comments,
            created_at=datetime.utcnow()
        )
        await self.workflow_history_repo.create(w_hist)

        return pr

    async def return_step(self, pr_id: int, user_id: int, comments: str) -> PurchaseRequisition:
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        active_step = await self.get_active_step(pr_id)

        # Return step
        active_step.status = "Returned"
        active_step.approver_id = user_id
        active_step.actioned_at = datetime.utcnow()
        await self.step_repo.update(active_step)

        # Return workflow
        workflow = await self.workflow_repo.get_by_pr_id(pr_id)
        workflow.status = "Returned for Modification"
        await self.workflow_repo.update(workflow)

        # Release budget reservation on return
        if pr.budget_code:
            await self.budget_service.release_budget(pr.pr_id)

        old_status = pr.status
        pr.status = "Returned for Modification"
        await self.pr_repo.update(pr)

        # Log approval history
        app_hist = ApprovalHistory(
            step_id=active_step.step_id,
            action="Return",
            performed_by=user_id,
            comments=comments,
            created_at=datetime.utcnow()
        )
        await self.approval_history_repo.create(app_hist)

        # Log workflow history
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Returned",
            performed_by=user_id,
            from_status=old_status,
            to_status="Returned for Modification",
            comments=comments,
            created_at=datetime.utcnow()
        )
        await self.workflow_history_repo.create(w_hist)

        return pr

    async def delegate_step(self, pr_id: int, user_id: int, delegate_to_user_id: int, comments: Optional[str] = None) -> PurchaseRequisition:
        active_step = await self.get_active_step(pr_id)

        # Delegate active step
        old_approver_id = active_step.approver_id
        active_step.approver_id = delegate_to_user_id
        await self.step_repo.update(active_step)

        # Log approval history
        app_hist = ApprovalHistory(
            step_id=active_step.step_id,
            action="Delegate",
            performed_by=user_id,
            comments=comments or f"Delegated to user {delegate_to_user_id}",
            created_at=datetime.utcnow()
        )
        await self.approval_history_repo.create(app_hist)

        # Log workflow history
        w_hist = WorkflowHistory(
            pr_id=pr_id,
            action="Delegated",
            performed_by=user_id,
            comments=comments or f"Delegated step {active_step.step_number} to user {delegate_to_user_id}",
            created_at=datetime.utcnow()
        )
        await self.workflow_history_repo.create(w_hist)

        return await self.pr_repo.get_by_id(pr_id)

    async def escalate_step(self, pr_id: int, user_id: int, comments: Optional[str] = None) -> PurchaseRequisition:
        active_step = await self.get_active_step(pr_id)

        # Escalate step to Admin role (role_id=4)
        active_step.approver_role_id = 4
        active_step.approver_id = None
        await self.step_repo.update(active_step)

        # Log approval history
        app_hist = ApprovalHistory(
            step_id=active_step.step_id,
            action="Escalate",
            performed_by=user_id,
            comments=comments or "Escalated step to Administrator",
            created_at=datetime.utcnow()
        )
        await self.approval_history_repo.create(app_hist)

        # Log workflow history
        w_hist = WorkflowHistory(
            pr_id=pr_id,
            action="Escalated",
            performed_by=user_id,
            comments=comments or f"Escalated step {active_step.step_number} to Admin",
            created_at=datetime.utcnow()
        )
        await self.workflow_history_repo.create(w_hist)

        return await self.pr_repo.get_by_id(pr_id)

    def _get_status_from_role_id(self, role_id: int) -> str:
        """
        Maps a role ID to its corresponding pending review status.
        """
        if role_id == 2:
            return "Pending Manager Approval"
        elif role_id == 3:
            return "Pending Finance Approval"
        elif role_id == 4:
            return "Pending CFO Approval"
        return "Under Review"
