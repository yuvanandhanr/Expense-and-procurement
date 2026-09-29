import uuid
from typing import List, Optional
from datetime import timezone, datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.purchase_requisition import PurchaseRequisition, PRItem
from src.models.approval import WorkflowHistory
from src.repositories.purchase_requisition import PRRepository, PRItemRepository
from src.repositories.approval import WorkflowHistoryRepository
from src.schemas.purchase_requisition import PRCreate, PRUpdate
from src.services.budget_service import BudgetService
from src.services.approval_service import ApprovalService


class PRService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.pr_repo = PRRepository(db)
        self.item_repo = PRItemRepository(db)
        self.history_repo = WorkflowHistoryRepository(db)
        self.budget_service = BudgetService(db)
        self.approval_service = ApprovalService(db)

    def generate_pr_number(self) -> str:
        """
        Generates a unique purchase requisition identifier, e.g. PR-20260803-A2E4BF
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"PR-{date_str}-{rand_str}"

    async def create_pr(self, data: PRCreate, requestor_id: int) -> PurchaseRequisition:
        """
        Creates a new draft purchase requisition with associated items.
        """
        # Calculate total estimated cost
        total_cost = Decimal("0.00")
        items_to_create = []

        for item_data in data.items:
            item_total = item_data.quantity * item_data.unit_price
            total_cost += item_total
            
            item = PRItem(
                category=item_data.category,
                item_name=item_data.item_name,
                specification=item_data.specification,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price
            )
            items_to_create.append(item)

        pr = PurchaseRequisition(
            pr_number=self.generate_pr_number(),
            title=data.title,
            justification=data.justification,
            department_id=data.department_id,
            cost_center_id=data.cost_center_id,
            budget_code=data.budget_code,
            priority=data.priority,
            purchase_type=data.purchase_type,
            need_by_date=data.need_by_date,
            project_code=data.project_code,
            requestor_id=requestor_id,
            status="Draft",
            total_estimated_amount=total_cost,
            created_at=datetime.utcnow()
        )

        pr = await self.pr_repo.create(pr)

        # Associate and create items
        for item in items_to_create:
            item.pr_id = pr.pr_id
            await self.item_repo.create(item)

        # Log initial creation in history
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Created",
            performed_by=requestor_id,
            from_status=None,
            to_status="Draft",
            comments="Purchase Requisition draft created",
            created_at=datetime.utcnow()
        )
        await self.history_repo.create(w_hist)

        # Reload eager loaded fields
        return await self.pr_repo.get_by_id(pr.pr_id)

    async def update_pr(self, pr_id: int, data: PRUpdate, user_id: int) -> PurchaseRequisition:
        """
        Updates an existing draft PR. Edits are rejected if the PR has already been submitted.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Requisition not found")

        if pr.status not in ("Draft", "Returned for Modification"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requisitions cannot be edited once submitted for review"
            )

        # Update basic fields
        update_dict = data.model_dump(exclude_unset=True, exclude={"items"})
        for k, v in update_dict.items():
            setattr(pr, k, v)

        # Update items if provided
        if data.items is not None:
            # Delete old items
            old_items = await self.item_repo.list_by_pr_id(pr_id)
            for item in old_items:
                await self.item_repo.delete(item.pr_item_id)

            # Re-create new items
            total_cost = Decimal("0.00")
            for item_data in data.items:
                item_total = item_data.quantity * item_data.unit_price
                total_cost += item_total
                
                item = PRItem(
                    pr_id=pr_id,
                    category=item_data.category,
                    item_name=item_data.item_name,
                    specification=item_data.specification,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_total
                )
                await self.item_repo.create(item)
            pr.total_estimated_amount = total_cost

        pr.updated_at = datetime.utcnow()
        await self.pr_repo.update(pr)

        return await self.pr_repo.get_by_id(pr_id)

    async def submit_pr(self, pr_id: int, user_id: int) -> PurchaseRequisition:
        """
        Submits a PR. Validates budget constraints, reserves funds, and initializes the approval workflow routing.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        if pr.status not in ("Draft", "Returned for Modification"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PR cannot be submitted from status: {pr.status}"
            )

        # Validate and reserve budget
        if pr.budget_code:
            await self.budget_service.reserve_budget(pr.pr_id, pr.budget_code, pr.total_estimated_amount)

        # Generate approval workflow routing chain
        await self.approval_service.generate_workflow(pr)

        return await self.pr_repo.get_by_id(pr_id)

    async def cancel_pr(self, pr_id: int, user_id: int) -> PurchaseRequisition:
        """
        Cancels a PR and releases any reserved budget allocations.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        if pr.status in ("Approved", "Rejected", "Cancelled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requisitions cannot be cancelled from status: {pr.status}"
            )

        old_status = pr.status

        # Release budget reservation
        if pr.budget_code:
            await self.budget_service.release_budget(pr.pr_id)

        # Terminate active approval workflows
        workflow = await self.approval_service.workflow_repo.get_by_pr_id(pr_id)
        if workflow:
            workflow.status = "Cancelled"
            await self.approval_service.workflow_repo.update(workflow)

            # Update active step
            active_step = await self.approval_service.step_repo.get_active_step_for_workflow(workflow.workflow_id)
            if active_step:
                active_step.status = "Skipped"
                await self.approval_service.step_repo.update(active_step)

        pr.status = "Cancelled"
        await self.pr_repo.update(pr)

        # Log to workflow history
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Cancelled",
            performed_by=user_id,
            from_status=old_status,
            to_status="Cancelled",
            comments="Purchase Requisition cancelled by user",
            created_at=datetime.utcnow()
        )
        await self.history_repo.create(w_hist)

        return pr

    async def clone_pr(self, pr_id: int, user_id: int) -> PurchaseRequisition:
        """
        Clones a rejected PR into a new Draft PR.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        if pr.status != "Rejected":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only rejected Purchase Requisitions can be cloned"
            )

        # Clone basic details into a new PR with a fresh number
        cloned_pr = PurchaseRequisition(
            pr_number=self.generate_pr_number(),
            title=f"Copy of: {pr.title or ''}",
            justification=pr.justification,
            department_id=pr.department_id,
            cost_center_id=pr.cost_center_id,
            budget_code=pr.budget_code,
            priority=pr.priority,
            purchase_type=pr.purchase_type,
            need_by_date=pr.need_by_date,
            project_code=pr.project_code,
            requestor_id=user_id,
            status="Draft",
            total_estimated_amount=pr.total_estimated_amount,
            created_at=datetime.utcnow()
        )

        cloned_pr = await self.pr_repo.create(cloned_pr)

        # Copy items
        items = await self.item_repo.list_by_pr_id(pr_id)
        for item in items:
            cloned_item = PRItem(
                pr_id=cloned_pr.pr_id,
                category=item.category,
                item_name=item.item_name,
                specification=item.specification,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price
            )
            await self.item_repo.create(cloned_item)

        # Log to workflow history
        w_hist = WorkflowHistory(
            pr_id=cloned_pr.pr_id,
            action="Created",
            performed_by=user_id,
            from_status=None,
            to_status="Draft",
            comments=f"Cloned from rejected PR ID {pr_id}",
            created_at=datetime.utcnow()
        )
        await self.history_repo.create(w_hist)

        return await self.pr_repo.get_by_id(cloned_pr.pr_id)

    async def allocate_inventory(self, pr_id: int, asset_id: int, user_id: int) -> PurchaseRequisition:
        """
        Admin allocates an existing asset from inventory to fulfill the PR.
        This resolves the PR without going to Procurement.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
        
        # Approve the Admin step
        active_step = await self.approval_service.get_active_step(pr_id)
        from src.models.auth import Role
        role_result = await self.db.execute(select(Role).where(Role.role_id == active_step.approver_role_id))
        step_role = role_result.scalar_one_or_none()
        if not step_role or step_role.role_name != "Admin":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Admin can allocate inventory at this step.")
            
        await self.approval_service.approve_step(pr_id, user_id, comments=f"Allocated Asset ID {asset_id} from inventory.")
        
        # Update PR
        pr.is_inventory_allocation = True
        pr.allocated_asset_id = asset_id
        pr.status = "Inventory Allocated"
        await self.pr_repo.update(pr)
        
        # Update Asset status (e.g. to Reserved or pending assignment)
        from src.models.assets import Asset
        asset_result = await self.db.execute(select(Asset).where(Asset.asset_id == asset_id))
        asset = asset_result.scalar_one_or_none()
        if asset:
            asset.status = "Assigned"
            asset.assigned_to = pr.requestor_id
        
        return pr

    async def initiate_procurement(self, pr_id: int, user_id: int) -> PurchaseRequisition:
        """
        Admin confirms no inventory available, escalates PR to Procurement/CFO.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
            
        # Add Step 3: CFO
        workflow = await self.approval_service.workflow_repo.get_by_pr_id(pr_id)
        cfo_role_id = await self.approval_service.get_role_id_by_name("CFO", 5)
        
        from src.models.approval import ApprovalStep
        step = ApprovalStep(
            workflow_id=workflow.workflow_id,
            step_number=3,
            approver_role_id=cfo_role_id,
            approver_id=None,
            status="Pending"
        )
        await self.approval_service.step_repo.create(step)
        
        # Approve Admin step
        await self.approval_service.approve_step(pr_id, user_id, comments="No inventory available. Initiating procurement.")
        
        pr.status = "Pending CFO Approval"
        await self.pr_repo.update(pr)
        
        return pr
