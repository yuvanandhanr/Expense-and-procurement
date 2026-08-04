from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.matching import ThreeWayMatching
from src.repositories.base import BaseRepository


class ThreeWayMatchingRepository(BaseRepository[ThreeWayMatching]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ThreeWayMatching, session)

    async def get_by_id(self, entity_id: int) -> Optional[ThreeWayMatching]:
        query = (
            select(self.model)
            .where(self.model.matching_id == entity_id)
            .options(
                selectinload(self.model.invoice),
                selectinload(self.model.po),
                selectinload(self.model.grn)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_invoice(self, invoice_id: int) -> Optional[ThreeWayMatching]:
        query = select(self.model).where(self.model.invoice_id == invoice_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
