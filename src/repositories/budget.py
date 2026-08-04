from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.budget import BudgetAllocation, BudgetReservation
from src.repositories.base import BaseRepository


class BudgetAllocationRepository(BaseRepository[BudgetAllocation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(BudgetAllocation, session)

    async def get_by_id(self, entity_id: int) -> Optional[BudgetAllocation]:
        return await self.session.get(self.model, entity_id)

    async def get_by_budget_code_id(self, budget_code_id: int) -> Optional[BudgetAllocation]:
        query = select(self.model).where(self.model.budget_code_id == budget_code_id, self.model.status == "Active")
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class BudgetReservationRepository(BaseRepository[BudgetReservation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(BudgetReservation, session)

    async def get_by_id(self, entity_id: int) -> Optional[BudgetReservation]:
        return await self.session.get(self.model, entity_id)

    async def get_by_pr_id(self, pr_id: int) -> List[BudgetReservation]:
        query = select(self.model).where(self.model.pr_id == pr_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
