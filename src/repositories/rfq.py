from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.rfq import RequestForQuotation, RFQItem, RFQVendor
from src.repositories.base import BaseRepository


class RFQRepository(BaseRepository[RequestForQuotation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RequestForQuotation, session)

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[RequestForQuotation]:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.rfq_vendors),
                selectinload(self.model.quotations)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, entity_id: int) -> Optional[RequestForQuotation]:
        query = (
            select(self.model)
            .where(self.model.rfq_id == entity_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.rfq_vendors),
                selectinload(self.model.quotations)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, rfq_number: str) -> Optional[RequestForQuotation]:
        query = select(self.model).where(self.model.rfq_number == rfq_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class RFQItemRepository(BaseRepository[RFQItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RFQItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[RFQItem]:
        return await self.session.get(self.model, entity_id)

    async def list_by_rfq(self, rfq_id: int) -> List[RFQItem]:
        query = select(self.model).where(self.model.rfq_id == rfq_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class RFQVendorRepository(BaseRepository[RFQVendor]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RFQVendor, session)

    async def get_by_id(self, entity_id: int) -> Optional[RFQVendor]:
        return await self.session.get(self.model, entity_id)

    async def list_by_rfq(self, rfq_id: int) -> List[RFQVendor]:
        query = select(self.model).where(self.model.rfq_id == rfq_id).options(selectinload(self.model.vendor))
        result = await self.session.execute(query)
        return list(result.scalars().all())
