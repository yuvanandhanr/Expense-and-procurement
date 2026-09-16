from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
        from src.services.notification_service import NotificationService
        self.notification_service = NotificationService(db)

    async def get_role_id_by_name(self, role_name: str, fallback_id: int) -> int:
        query = select(Role).where(Role.role_name == role_name)
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        return role.role_id if role else fallback_id

    async def initialize_approval_flow(self, document_type: str, document_id: int, amount: Decimal, department_id: Optional[int] = None):
        if document_type == "PurchaseRequisition":
            pr = await self.pr_repo.get_by_id(document_id)
            if not pr:
                raise ValueError("PR not found")
            return await self.generate_workflow(pr)
        if document_type == "ExpenseReport":
            from src.models.expense import ExpenseReport, ExpenseApproval
            from src.models.auth import User, Role
            
            query = select(ExpenseReport).where(ExpenseReport.expense_report_id == document_id)
            result = await self.db.execute(query)
            report = result.scalar_one_or_none()
            
            if not report:
                raise ValueError("Expense report not found")
                
            query_user = select(User).where(User.user_id == report.employee_id).options(selectinload(User.roles))
            result_user = await self.db.execute(query_user)
            requestor = result_user.scalar_one_or_none()
            manager_id = requestor.manager_id if requestor else None
            
            requestor_roles = {r.role_name for r in requestor.roles} if requestor else set()
            
            # If requestor is a Manager, Admin, CFO, CEO, or Finance Manager
            if requestor_roles & {"Manager", "Admin", "CFO", "CEO", "Finance Manager"}:
                target_roles = []
                
                if "CEO" in requestor_roles:
                    target_roles = ["CFO"]
                    report.status = "Pending CFO Approval"
                elif "Admin" in requestor_roles:
                    target_roles = ["CFO"]
                    report.status = "Pending CFO Approval"
                elif "Finance Manager" in requestor_roles or "Finance" in requestor_roles:
                    target_roles = ["CFO"]
                    report.status = "Pending CFO Approval"
                elif "CFO" in requestor_roles:
                    # Keep CFO logic unchanged as requested
                    target_roles = ["Finance Manager", "Finance"]
                    report.status = "Pending Finance Manager Approval"
                elif "Manager" in requestor_roles:
                    target_roles = ["Finance Manager", "Finance"]
                    report.status = "Pending Finance Manager Approval"

                # Find an approver who is NOT the requestor
                fm_query = select(User).join(User.roles).where(
                    Role.role_name.in_(target_roles),
                    User.status == "Active",
                    User.user_id != requestor.user_id
                )
                fm_result = await self.db.execute(fm_query)
                next_approver = fm_result.scalars().first()
                approver_id = next_approver.user_id if next_approver else None
                
                approval_entry = ExpenseApproval(
                    expense_report_id=report.expense_report_id,
                    approver_id=approver_id,
                    status="Pending"
                )
                self.db.add(approval_entry)
            else:
                # Employee submits -> Manager
                approver_id = manager_id
                # Enforce that approver cannot be the requestor
                if approver_id == requestor.user_id:
                    approver_id = None
                    
                approval_entry = ExpenseApproval(
                    expense_report_id=report.expense_report_id,
                    approver_id=approver_id,
                    status="Pending"
                )
                self.db.add(approval_entry)
                report.status = "Pending Manager Approval"
            
            if approver_id:
                try:
                    await self.notification_service.send_notification(
                        user_id=approver_id,
                        template_name="ExpenseApprovalRequestAlert",
                        context={"report_id": report.expense_report_id, "amount": str(report.total_amount)}
                    )
                except Exception:
                    pass
            
            return approval_entry
        else:
            raise ValueError(f"Unknown document type: {document_type}")

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
        
        # Get requestor's manager_id
        from src.models.auth import User
        query_user = select(User).where(User.user_id == pr.requestor_id).options(selectinload(User.roles))
        result_user = await self.db.execute(query_user)
        requestor = result_user.scalar_one_or_none()
        manager_id = requestor.manager_id if requestor else None
        
        requestor_is_cfo = False
        requestor_is_fm = False
        requestor_is_admin = False
        requestor_is_ceo = False
        if requestor:
            requestor_is_cfo = any(r.role_name == "CFO" for r in requestor.roles)
            requestor_is_fm = any(r.role_name in ["Finance Manager", "Finance"] for r in requestor.roles)
            requestor_is_admin = any(r.role_name == "Admin" for r in requestor.roles)
            requestor_is_ceo = any(r.role_name == "CEO" for r in requestor.roles)

        admin_role_id = await self.get_role_id_by_name("Admin", 4)
        manager_role_id = await self.get_role_id_by_name("Manager", 2)

        step_counter = 1
        
        # Step 1: Manager Approval (Skip if requestor is CEO or has no manager)
        if manager_id and manager_id != pr.requestor_id and not requestor_is_ceo:
            steps_to_create.append({"step_number": step_counter, "approver_role_id": manager_role_id, "approver_id": manager_id})
            step_counter += 1

        # Step 2: Admin Approval (Inventory Check)
        steps_to_create.append({"step_number": step_counter, "approver_role_id": admin_role_id, "approver_id": None})

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
        pr.status = await self._get_status_from_role_id(first_step_role_id)
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

        # Notify Reporting Manager
        if manager_id:
            await self.notification_service.send_notification(
                user_id=manager_id,
                template_name="ApprovalRequestAlert",
                context={"pr_number": pr.pr_number, "justification": pr.justification}
            )

        return workflow

    async def get_pending_approvals_for_user(self, user: User) -> List[dict]:
        from src.models.auth import User as UserModel
        
        user_role_ids = [role.role_id for role in user.roles]
        is_admin = any(role.role_name == "Admin" for role in user.roles)

        # Cross-wire "Finance" and "Finance Manager" role IDs
        has_finance = any(r.role_name in ["Finance", "Finance Manager"] for r in user.roles)
        if has_finance:
            res = await self.db.execute(select(Role.role_id).where(Role.role_name.in_(["Finance", "Finance Manager"])))
            extra_ids = res.scalars().all()
            for eid in extra_ids:
                if eid not in user_role_ids:
                    user_role_ids.append(eid)

        query = (
            select(ApprovalWorkflow, PurchaseRequisition, UserModel)
            .join(PurchaseRequisition, ApprovalWorkflow.pr_id == PurchaseRequisition.pr_id)
            .join(UserModel, PurchaseRequisition.requestor_id == UserModel.user_id)
            .where(
                PurchaseRequisition.total_estimated_amount > 0
            )
            .order_by(ApprovalWorkflow.created_at.desc())
        )

        result = await self.db.execute(query)
        workflows_data = result.all()
        
        if not workflows_data:
            return []
            
        wf_ids = [w[0].workflow_id for w in workflows_data]
        steps_query = select(ApprovalStep).where(ApprovalStep.workflow_id.in_(wf_ids))
        steps_res = await self.db.execute(steps_query)
        all_steps = steps_res.scalars().all()
        
        steps_by_wf = {}
        step_to_wf = {}
        for s in all_steps:
            steps_by_wf.setdefault(s.workflow_id, []).append(s)
            step_to_wf[s.step_id] = s.workflow_id
            
        step_ids = [s.step_id for s in all_steps]
        hist_query = select(ApprovalHistory).where(ApprovalHistory.step_id.in_(step_ids))
        hist_res = await self.db.execute(hist_query)
        all_history = hist_res.scalars().all()
        
        history_by_wf = {}
        for h in all_history:
            wf_id = step_to_wf.get(h.step_id)
            if wf_id:
                history_by_wf.setdefault(wf_id, []).append(h)
                
        user_query = select(UserModel)
        user_res = await self.db.execute(user_query)
        users_by_id = {u.user_id: u for u in user_res.scalars().all()}
        
        role_query = select(Role)
        role_res = await self.db.execute(role_query)
        roles_by_id = {r.role_id: r.role_name for r in role_res.scalars().all()}

        pending_workflows = []
        is_ceo_or_cfo = any(role.role_name in ["CEO", "CFO"] for role in user.roles)

        for workflow, pr, requestor in workflows_data:
            wf_steps = steps_by_wf.get(workflow.workflow_id, [])
            pending_steps = [s for s in wf_steps if s.status == "Pending"]
            active_step = min(pending_steps, key=lambda x: x.step_number) if pending_steps else None

            can_approve = False
            if active_step:
                if is_admin:
                    can_approve = True
                elif active_step.approver_id == user.user_id:
                    can_approve = True
                elif active_step.approver_id is None and active_step.approver_role_id in user_role_ids:
                    can_approve = True

            can_view = False
            if is_admin or is_ceo_or_cfo:
                can_view = True
            elif can_approve:
                can_view = True
            elif pr.requestor_id == user.user_id:
                can_view = True
            else:
                wf_hist = history_by_wf.get(workflow.workflow_id, [])
                if any(h.performed_by == user.user_id for h in wf_hist):
                    can_view = True

            if can_view:
                wf_hist = history_by_wf.get(workflow.workflow_id, [])
                past_approvers = []
                for h in wf_hist:
                    if h.action == "Approve" and h.performed_by in users_by_id:
                        u = users_by_id[h.performed_by]
                        step = next((s for s in wf_steps if s.step_id == h.step_id), None)
                        role_name = roles_by_id.get(step.approver_role_id, "Approver") if step else "Approver"
                        past_approvers.append(f"{role_name} ({u.first_name} {u.last_name})")
                        
                pending_approvers = []
                for s in pending_steps:
                    role_name = roles_by_id.get(s.approver_role_id, "Approver")
                    pending_approvers.append(role_name)
                        
                current_step_sequence = active_step.step_number if active_step else (max(s.step_number for s in wf_steps) if wf_steps else 0)
                steps_to_return = [active_step] if active_step else wf_steps

                pending_workflows.append({
                    "workflow_id": workflow.workflow_id,
                    "entity_type": "PurchaseRequisition",
                    "entity_id": pr.pr_id,
                    "current_step_sequence": current_step_sequence,
                    "status": workflow.status,
                    "created_at": workflow.created_at,
                    "updated_at": workflow.updated_at,
                    "requestor_id": pr.requestor_id,
                    "requestor_name": f"{requestor.first_name} {requestor.last_name}",
                    "title": pr.title,
                    "justification": pr.justification,
                    "total_amount": pr.total_estimated_amount,
                    "amount": pr.total_estimated_amount,
                    "past_approvers": past_approvers,
                    "pending_approvers": pending_approvers,
                    "steps": steps_to_return,
                    "can_approve": can_approve
                })

        return pending_workflows

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

    async def approve_step(self, pr_id: int, user_id: int, comments: Optional[str] = None, physical_inspection_done: bool = False) -> PurchaseRequisition:
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        active_step = await self.get_active_step(pr_id)

        # Self-approval prevention
        if user_id == pr.requestor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users cannot approve their own requests."
            )

        # Physical inspection enforcement for Managers
        from src.models.auth import Role
        role_result = await self.db.execute(select(Role).where(Role.role_id == active_step.approver_role_id))
        step_role = role_result.scalar_one_or_none()
        if step_role and step_role.role_name == "Manager":
            if not physical_inspection_done:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Physical inspection must be completed to approve this request."
                )

        # Duplicate approval prevention
        existing_approval_query = select(ApprovalHistory).where(
            ApprovalHistory.step_id.in_(
                select(ApprovalStep.step_id).where(ApprovalStep.workflow_id == active_step.workflow_id)
            ),
            ApprovalHistory.performed_by == user_id,
            ApprovalHistory.action == "Approve"
        )
        result_existing = await self.db.execute(existing_approval_query)
        if result_existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate approval: You have already approved a step in this workflow."
            )

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
            pr.status = await self._get_status_from_role_id(next_step.approver_role_id)
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
            
            # Notify next approvers
            from src.models.auth import User, Role
            query_next = select(User).join(User.roles).where(Role.role_id == next_step.approver_role_id)
            next_users = (await self.db.execute(query_next)).scalars().all()
            for nu in next_users:
                await self.notification_service.send_notification(
                    user_id=nu.user_id,
                    template_name="ApprovalRequestAlert",
                    context={"pr_number": pr.pr_number, "justification": pr.justification}
                )
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
            
            # Notify Procurement Team
            # Auto-generate RFQ and invite active vendors
            from src.services.rfq_service import RFQService
            from src.schemas.rfq import RFQCreate, RFQItemCreate
            from src.models.vendor import Vendor
            from datetime import timedelta
            
            # Fetch all active vendors
            query_vendors = select(Vendor.vendor_id).where(Vendor.status == "Active", Vendor.blacklist_status == False)
            active_vendor_ids = (await self.db.execute(query_vendors)).scalars().all()
            
            # Create RFQ payload
            rfq_items = []
            for item in pr.items:
                rfq_items.append(RFQItemCreate(
                    pr_item_id=item.pr_item_id,
                    item_name=item.item_name,
                    specification=item.specification,
                    quantity=item.quantity
                ))
            
            rfq_payload = RFQCreate(
                title=f"RFQ for PR: {pr.title}",
                description=pr.justification,
                pr_id=pr.pr_id,
                submission_deadline=datetime.utcnow() + timedelta(days=7),
                invited_vendor_ids=list(active_vendor_ids)[:3],
                items=rfq_items
            )
            try:
                rfq_service = RFQService(self.db)
                await rfq_service.create_rfq(rfq_payload, user_id)
            except Exception:
                pass

        return await self.pr_repo.get_by_id(pr_id)

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
        
        # Notify Employee
        if pr.requestor_id:
            await self.notification_service.send_notification(
                user_id=pr.requestor_id,
                template_name="ApprovalCompletedAlert",
                context={"pr_number": pr.pr_number, "status": "Rejected"}
            )

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

        # Notify Employee
        if pr.requestor_id:
            await self.notification_service.send_notification(
                user_id=pr.requestor_id,
                template_name="ApprovalCompletedAlert",
                context={"pr_number": pr.pr_number, "status": "Returned for Modification"}
            )

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

    async def cancel_workflow(self, workflow_id: int, user_id: int, comments: str = "Cancelled by requestor") -> bool:
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
            
        pr = await self.pr_repo.get_by_id(workflow.pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Requisition not found")
            
        if pr.requestor_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the requestor can cancel this approval")
            
        # Cancel workflow
        workflow.status = "Cancelled"
        await self.workflow_repo.update(workflow)
        
        old_status = pr.status
        pr.status = "Cancelled"
        await self.pr_repo.update(pr)
        
        # Release budget reservation
        if pr.budget_code:
            await self.budget_service.release_budget(pr.pr_id)
            
        # Log workflow history
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Cancelled",
            performed_by=user_id,
            from_status=old_status,
            to_status="Cancelled",
            comments=comments,
            created_at=datetime.utcnow()
        )
        await self.workflow_history_repo.create(w_hist)
        
        return True

    async def _get_status_from_role_id(self, role_id: int) -> str:
        """
        Maps a role ID to its corresponding pending review status dynamically.
        """
        from src.models.auth import Role
        query = select(Role).where(Role.role_id == role_id)
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()
        
        if role:
            if role.role_name in ["Finance", "Finance Manager"]:
                return "Pending Finance Approval"
            return f"Pending {role.role_name} Approval"
        return "Under Review"
