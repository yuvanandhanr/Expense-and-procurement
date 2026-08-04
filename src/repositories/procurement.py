from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.procurement import ProcurementClosure
from src.repositories.base import BaseRepository


class ProcurementClosureRepository(BaseRepository[ProcurementClosure]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProcurementClosure, session)

    async def get_by_id(self, entity_id: int) -> Optional[ProcurementClosure]:
        query = (
            select(self.model)
            .where(self.model.closure_id == entity_id)
            .options(
                selectinload(self.model.po)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_po(self, po_id: int) -> Optional[ProcurementClosure]:
        query = select(self.model).where(self.model.po_id == po_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
