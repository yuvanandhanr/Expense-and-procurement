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
            unit_price_dec = Decimal(str(item_data.unit_price))
            item_total = Decimal(str(item_data.quantity)) * unit_price_dec
            total_cost += item_total
            
            item = PRItem(
                category=item_data.category,
                item_name=item_data.item_name,
                specification=item_data.specification,
                quantity=item_data.quantity,
                unit_price=unit_price_dec
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

        if pr.status not in ("Draft", "Returned for Modification", "Returned for Correction"):
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

        if pr.status not in ("Draft", "Returned for Modification", "Returned for Correction"):
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

    async def check_inventory(self, pr_id: int) -> dict:
        """
        Admin Inventory Verification:
        Case A: Asset availability is more than 4 (> 4)
        Case B: Asset availability is 4 or fewer (<= 4), or the asset is unavailable
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        from src.models.assets import Asset
        from sqlalchemy.orm import selectinload

        query = select(Asset).where(
            Asset.status.in_(["Available", "Unassigned", "In Stock"])
        ).options(selectinload(Asset.category))
        res = await self.db.execute(query)
        available_assets = res.scalars().all()

        items_detail = []
        min_available = 999999 if pr.items else 0

        for item in pr.items:
            req_name = item.item_name.strip().lower()
            matching = []
            for a in available_assets:
                asset_model = (a.model or "").strip().lower()
                cat_name = (a.category.category_name if a.category else "").strip().lower()
                if (
                    req_name in asset_model 
                    or asset_model in req_name 
                    or (item.category and item.category.strip().lower() in cat_name)
                    or (a.asset_number and req_name in a.asset_number.strip().lower())
                ):
                    matching.append({
                        "asset_id": a.asset_id,
                        "asset_number": a.asset_number,
                        "asset_tag": a.asset_tag,
                        "model": a.model or a.asset_number,
                        "serial_number": a.serial_number or a.asset_tag,
                        "status": a.status,
                        "category": cat_name
                    })

            count = len(matching)
            if count < min_available:
                min_available = count
            items_detail.append({
                "pr_item_id": item.pr_item_id,
                "item_name": item.item_name,
                "category": item.category,
                "quantity": item.quantity,
                "available_count": count,
                "available_assets": matching
            })

        if not pr.items:
            min_available = 0

        is_case_a = min_available > 4
        return {
            "pr_id": pr.pr_id,
            "pr_number": pr.pr_number,
            "pr_title": pr.title,
            "available_count": min_available,
            "case": "A" if is_case_a else "B",
            "can_allocate_directly": is_case_a,
            "requires_procurement_prompt": not is_case_a,
            "items": items_detail
        }

    async def allocate_inventory(self, pr_id: int, asset_id: Optional[int], user_id: int) -> PurchaseRequisition:
        """
        Case A (or explicit Admin allocation):
        Admin approves the requisition. The requested asset is assigned to the employee.
        The requisition process ends here without initiating procurement.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        active_step = await self.approval_service.get_active_step(pr_id)
        from src.models.auth import Role
        role_result = await self.db.execute(select(Role).where(Role.role_id == active_step.approver_role_id))
        step_role = role_result.scalar_one_or_none()
        if not step_role or step_role.role_name not in ["Admin", "SuperAdmin"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Admin can allocate inventory at this step.")

        from src.models.assets import Asset, AssetAssignment
        from src.models.approval import ApprovalHistory, WorkflowHistory
        from datetime import date

        selected_asset = None
        if asset_id:
            asset_res = await self.db.execute(select(Asset).where(Asset.asset_id == asset_id))
            selected_asset = asset_res.scalar_one_or_none()
            if not selected_asset or selected_asset.status not in ["Available", "Unassigned", "In Stock"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected asset is not available in inventory.")
        else:
            # Auto-pick first matching available asset
            inv_info = await self.check_inventory(pr_id)
            matching_assets = []
            for itm in inv_info.get("items", []):
                matching_assets.extend(itm.get("available_assets", []))
            if not matching_assets:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No matching available asset found in inventory.")
            first_match_id = matching_assets[0]["asset_id"]
            asset_res = await self.db.execute(select(Asset).where(Asset.asset_id == first_match_id))
            selected_asset = asset_res.scalar_one_or_none()

        if not selected_asset:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve an asset from inventory.")

        # 1. Update Asset to Assigned to requestor
        selected_asset.status = "Assigned"
        selected_asset.assigned_employee_id = pr.requestor_id

        # 2. Create AssetAssignment record
        assignment = AssetAssignment(
            asset_id=selected_asset.asset_id,
            assigned_to=pr.requestor_id,
            assigned_by=user_id,
            assigned_date=date.today(),
            status="Active",
            notes=f"Allocated from inventory for Requisition #{pr.pr_number}"
        )
        self.db.add(assignment)

        # 3. Mark Admin step approved
        active_step.status = "Approved"
        active_step.approver_id = user_id
        active_step.actioned_at = datetime.utcnow()
        await self.approval_service.step_repo.update(active_step)

        # 3b. Record approval history for Admin
        app_hist = ApprovalHistory(
            step_id=active_step.step_id,
            action="Approve",
            performed_by=user_id,
            comments=f"Direct Inventory Allocation: Assigned {selected_asset.model or selected_asset.asset_number} (ID: {selected_asset.asset_id}) to employee.",
            created_at=datetime.utcnow()
        )
        await self.approval_service.approval_history_repo.create(app_hist)

        # 4. Complete workflow (Requisition process ends here!)
        workflow = await self.approval_service.workflow_repo.get_by_pr_id(pr_id)
        workflow.status = "Approved"
        await self.approval_service.workflow_repo.update(workflow)

        pr.is_inventory_allocation = True
        pr.allocated_asset_id = selected_asset.asset_id
        pr.status = "Approved"
        await self.pr_repo.update(pr)

        # 5. Workflow history log
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Approved",
            performed_by=user_id,
            from_status="Pending Admin Approval",
            to_status="Approved",
            comments=f"Direct Inventory Allocation: Assigned {selected_asset.model or selected_asset.asset_number} (ID: {selected_asset.asset_id}) to employee. Requisition process completed.",
            created_at=datetime.utcnow()
        )
        await self.approval_service.workflow_history_repo.create(w_hist)

        # 6. Notify requestor
        if pr.requestor_id:
            await self.approval_service.notification_service.send_notification(
                user_id=pr.requestor_id,
                template_name="ApprovalCompletedAlert",
                context={
                    "pr_number": pr.pr_number,
                    "status": "Approved - Asset Assigned from Inventory"
                }
            )

        return pr

    async def initiate_procurement(self, pr_id: int, user_id: int) -> PurchaseRequisition:
        """
        Case B: Asset availability is 4 or fewer, or asset is unavailable.
        Admin confirmed Yes to send procurement request to Finance Manager.
        Forwards the procurement request to the Finance Manager with notification.
        """
        pr = await self.pr_repo.get_by_id(pr_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

        active_step = await self.approval_service.get_active_step(pr_id)
        from src.models.auth import Role, User
        role_result = await self.db.execute(select(Role).where(Role.role_id == active_step.approver_role_id))
        step_role = role_result.scalar_one_or_none()
        if not step_role or step_role.role_name not in ["Admin", "SuperAdmin"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Admin can forward procurement requests to Finance Manager.")

        # Step 3: Add/route to Finance Manager
        workflow = await self.approval_service.workflow_repo.get_by_pr_id(pr_id)
        fm_role_id = await self.approval_service.get_role_id_by_name("Finance Manager", 6)

        from src.models.approval import ApprovalStep, WorkflowHistory, ApprovalHistory
        existing_steps_query = select(ApprovalStep).where(ApprovalStep.workflow_id == workflow.workflow_id)
        existing_steps = (await self.db.execute(existing_steps_query)).scalars().all()
        max_step = max((s.step_number for s in existing_steps), default=2)

        fm_step = next((s for s in existing_steps if s.approver_role_id == fm_role_id), None)
        if not fm_step:
            fm_step = ApprovalStep(
                workflow_id=workflow.workflow_id,
                step_number=max_step + 1,
                approver_role_id=fm_role_id,
                approver_id=None,
                status="Pending"
            )
            await self.approval_service.step_repo.create(fm_step)
        else:
            fm_step.status = "Pending"
            await self.approval_service.step_repo.update(fm_step)

        # Approve Admin step
        active_step.status = "Approved"
        active_step.approver_id = user_id
        active_step.actioned_at = datetime.utcnow()
        await self.approval_service.step_repo.update(active_step)

        # Record approval history for Admin
        app_hist = ApprovalHistory(
            step_id=active_step.step_id,
            action="Approve",
            performed_by=user_id,
            comments="Inventory verification completed (stock <= 4). Procurement request forwarded to Finance Manager.",
            created_at=datetime.utcnow()
        )
        await self.approval_service.approval_history_repo.create(app_hist)

        # Update PR status
        old_status = pr.status
        pr.status = "Pending Finance Manager Approval"
        await self.pr_repo.update(pr)

        # Workflow history
        w_hist = WorkflowHistory(
            pr_id=pr.pr_id,
            action="Procurement Requested",
            performed_by=user_id,
            from_status=old_status,
            to_status=pr.status,
            comments="Inventory verification completed (stock <= 4). Procurement request forwarded to Finance Manager.",
            created_at=datetime.utcnow()
        )
        await self.approval_service.workflow_history_repo.create(w_hist)

        # Notify Finance Manager explaining which asset needs to be purchased and required quantity
        items_summary = ", ".join(f"{it.quantity}x {it.item_name}" for it in pr.items) if pr.items else pr.title
        query_fm = select(User).join(User.roles).where(Role.role_name == "Finance Manager")
        fm_users = (await self.db.execute(query_fm)).scalars().all()
        for fm in fm_users:
            await self.approval_service.notification_service.send_notification(
                user_id=fm.user_id,
                template_name="ApprovalRequestAlert",
                context={
                    "pr_number": pr.pr_number,
                    "justification": f"Procurement required: {items_summary}. Admin confirmed low/unavailable inventory."
                }
            )

        return pr
