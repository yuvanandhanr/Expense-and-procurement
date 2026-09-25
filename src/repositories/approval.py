from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.approval import (
    ApprovalMatrix,
    ApprovalWorkflow,
    ApprovalStep,
    WorkflowHistory,
    ApprovalHistory,
    ApprovalComment,
)
from src.repositories.base import BaseRepository


class ApprovalMatrixRepository(BaseRepository[ApprovalMatrix]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApprovalMatrix, session)

    async def get_by_id(self, entity_id: int) -> Optional[ApprovalMatrix]:
        return await self.session.get(self.model, entity_id)

    async def find_matching_rules(
        self,
        department_id: Optional[int],
        cost_center_id: Optional[int],
        purchase_type: Optional[str],
        amount: float
    ) -> List[ApprovalMatrix]:
        """
        Finds rules matching requisition parameters sorted by approval level.
        """
        filters = []
        if department_id is not None:
            filters.append(self.model.department_id == department_id)
        if cost_center_id is not None:
            filters.append(self.model.cost_center_id == cost_center_id)
        if purchase_type is not None:
            filters.append(self.model.purchase_type == purchase_type)
            
        filters.append(self.model.min_amount <= amount)
        filters.append(self.model.max_amount >= amount)

        query = select(self.model).where(and_(*filters)).order_by(self.model.approval_level.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ApprovalWorkflowRepository(BaseRepository[ApprovalWorkflow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApprovalWorkflow, session)

    async def get_by_id(self, entity_id: int) -> Optional[ApprovalWorkflow]:
        query = (
            select(self.model)
            .where(self.model.workflow_id == entity_id)
            .options(selectinload(self.model.steps))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_pr_id(self, pr_id: int) -> Optional[ApprovalWorkflow]:
        query = (
            select(self.model)
            .where(self.model.pr_id == pr_id)
            .order_by(self.model.created_at.desc())
            .options(selectinload(self.model.steps))
        )
        result = await self.session.execute(query)
        return result.scalars().first()


class ApprovalStepRepository(BaseRepository[ApprovalStep]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApprovalStep, session)

    async def get_by_id(self, entity_id: int) -> Optional[ApprovalStep]:
        query = (
            select(self.model)
            .where(self.model.step_id == entity_id)
            .options(
                selectinload(self.model.workflow),
                selectinload(self.model.approver),
                selectinload(self.model.approver_role)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_step_for_workflow(self, workflow_id: int) -> Optional[ApprovalStep]:
        """
        Retrieves the first pending step in order of step_number.
        """
        query = (
            select(self.model)
            .where(self.model.workflow_id == workflow_id, self.model.status == "Pending")
            .order_by(self.model.step_number.asc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class WorkflowHistoryRepository(BaseRepository[WorkflowHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(WorkflowHistory, session)

    async def get_by_id(self, entity_id: int) -> Optional[WorkflowHistory]:
        return await self.session.get(self.model, entity_id)

    async def list_by_pr_id(self, pr_id: int) -> List[WorkflowHistory]:
        query = (
            select(self.model)
            .where(self.model.pr_id == pr_id)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ApprovalHistoryRepository(BaseRepository[ApprovalHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApprovalHistory, session)

    async def get_by_id(self, entity_id: int) -> Optional[ApprovalHistory]:
        return await self.session.get(self.model, entity_id)


class CommentRepository(BaseRepository[ApprovalComment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApprovalComment, session)

    async def get_by_id(self, entity_id: int) -> Optional[ApprovalComment]:
        query = (
            select(self.model)
            .where(self.model.comment_id == entity_id)
            .options(selectinload(self.model.replies))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_pr_id(self, pr_id: int, include_internal: bool = False) -> List[ApprovalComment]:
        filters = [self.model.pr_id == pr_id, self.model.parent_comment_id == None]
        if not include_internal:
            filters.append(self.model.is_internal == False)

        query = (
            select(self.model)
            .where(and_(*filters))
            .options(selectinload(self.model.replies))
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
