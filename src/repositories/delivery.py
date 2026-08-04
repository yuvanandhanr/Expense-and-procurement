from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.delivery import Delivery, DeliveryItem
from src.repositories.base import BaseRepository


class DeliveryRepository(BaseRepository[Delivery]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Delivery, session)

    async def get_by_id(self, entity_id: int) -> Optional[Delivery]:
        query = (
            select(self.model)
            .where(self.model.delivery_id == entity_id)
            .options(selectinload(self.model.items))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, delivery_number: str) -> Optional[Delivery]:
        query = select(self.model).where(self.model.delivery_number == delivery_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class DeliveryItemRepository(BaseRepository[DeliveryItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DeliveryItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[DeliveryItem]:
        return await self.session.get(self.model, entity_id)
