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
