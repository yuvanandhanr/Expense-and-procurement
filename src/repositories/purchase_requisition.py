from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.purchase_requisition import PurchaseRequisition, PRItem
from src.repositories.base import BaseRepository


class PRRepository(BaseRepository[PurchaseRequisition]):
    """
    Repository for PurchaseRequisition CRUD operations.
    """
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PurchaseRequisition, session)

    async def get_by_id(self, entity_id: int) -> Optional[PurchaseRequisition]:
        """
        Retrieves a purchase requisition by ID, eager loading items and relations.
        """
        query = (
            select(self.model)
            .where(self.model.pr_id == entity_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.requestor),
                selectinload(self.model.department),
                selectinload(self.model.cost_center)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_requestor(self, requestor_id: int) -> List[PurchaseRequisition]:
        """
        Lists all purchase requisitions created by a specific user.
        """
        query = (
            select(self.model)
            .where(self.model.requestor_id == requestor_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.requestor)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_department(self, department_id: int) -> List[PurchaseRequisition]:
        """
        Lists all purchase requisitions in a given department.
        """
        query = (
            select(self.model)
            .where(self.model.department_id == department_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.requestor)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[PurchaseRequisition]:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.requestor)
            )
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class PRItemRepository(BaseRepository[PRItem]):
    """
    Repository for PRItem CRUD operations.
    """
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PRItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[PRItem]:
        return await self.session.get(self.model, entity_id)

    async def list_by_pr_id(self, pr_id: int) -> List[PRItem]:
        query = select(self.model).where(self.model.pr_id == pr_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_accessible_prs(self, user) -> List[PurchaseRequisition]:
        from src.models.approval import ApprovalWorkflow, ApprovalStep, ApprovalHistory
        from src.models.auth import User as UserModel, Role
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload

        user_roles = [r.role_id for r in user.roles]
        
        stmt = (
            select(self.model)
            .outerjoin(UserModel, self.model.requestor_id == UserModel.user_id)
            .outerjoin(ApprovalWorkflow, ApprovalWorkflow.pr_id == self.model.pr_id)
            .outerjoin(ApprovalStep, ApprovalStep.workflow_id == ApprovalWorkflow.workflow_id)
            .outerjoin(ApprovalHistory, ApprovalHistory.step_id == ApprovalStep.step_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.requestor)
            )
        )
        
        conditions = [self.model.requestor_id == user.user_id]
        
        # If manager, can see direct reports
        user_role_names = [r.role_name for r in user.roles]
        if "Manager" in user_role_names:
            manager_cond = (UserModel.manager_id == user.user_id) & (self.model.status != "Draft")
            if not any(r in user_role_names for r in ["Admin", "SuperAdmin", "CEO", "CFO"]):
                manager_cond = manager_cond & (~UserModel.roles.any(Role.role_name.in_(["Admin", "CFO", "CEO", "Finance Manager"])))
            conditions.append(manager_cond)
            
        # In approval step or history
        conditions.append((ApprovalStep.approver_id == user.user_id) & (self.model.status != "Draft"))
        conditions.append((ApprovalStep.approver_id.is_(None)) & (ApprovalStep.approver_role_id.in_(user_roles)) & (self.model.status != "Draft"))
        conditions.append((ApprovalHistory.performed_by == user.user_id) & (self.model.status != "Draft"))
        
        stmt = stmt.where(or_(*conditions)).order_by(self.model.created_at.desc())
        result = await self.session.execute(stmt)
        
        # Deduplicate
        seen = set()
        prs = []
        for pr in result.scalars().all():
            if pr.pr_id not in seen:
                seen.add(pr.pr_id)
                prs.append(pr)
        return prs
