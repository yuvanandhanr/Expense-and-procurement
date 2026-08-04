from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.grn import GoodsReceipt, GoodsReceiptItem
from src.repositories.base import BaseRepository


class GRNRepository(BaseRepository[GoodsReceipt]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(GoodsReceipt, session)

    async def get_by_id(self, entity_id: int) -> Optional[GoodsReceipt]:
        query = (
            select(self.model)
            .where(self.model.grn_id == entity_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.po)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, grn_number: str) -> Optional[GoodsReceipt]:
        query = select(self.model).where(self.model.grn_number == grn_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class GRNItemRepository(BaseRepository[GoodsReceiptItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(GoodsReceiptItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[GoodsReceiptItem]:
        return await self.session.get(self.model, entity_id)
