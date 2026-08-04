from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.inspection import InspectionReport, InspectionItem
from src.repositories.base import BaseRepository


class InspectionRepository(BaseRepository[InspectionReport]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InspectionReport, session)

    async def get_by_id(self, entity_id: int) -> Optional[InspectionReport]:
        query = (
            select(self.model)
            .where(self.model.inspection_id == entity_id)
            .options(selectinload(self.model.items))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class InspectionItemRepository(BaseRepository[InspectionItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InspectionItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[InspectionItem]:
        return await self.session.get(self.model, entity_id)
