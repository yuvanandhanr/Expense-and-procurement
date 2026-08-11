from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.quotation import VendorQuotation, QuotationItem, QuotationComparison
from src.repositories.base import BaseRepository


class QuotationRepository(BaseRepository[VendorQuotation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VendorQuotation, session)

    async def get_by_id(self, entity_id: int) -> Optional[VendorQuotation]:
        query = (
            select(self.model)
            .where(self.model.quotation_id == entity_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.vendor)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, quotation_number: str) -> Optional[VendorQuotation]:
        query = select(self.model).where(self.model.quotation_number == quotation_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_rfq(self, rfq_id: int) -> List[VendorQuotation]:
        query = (
            select(self.model)
            .where(self.model.rfq_id == rfq_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.vendor)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_vendor(self, vendor_id: int) -> List[VendorQuotation]:
        query = (
            select(self.model)
            .where(self.model.vendor_id == vendor_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.vendor)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class QuotationItemRepository(BaseRepository[QuotationItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(QuotationItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[QuotationItem]:
        return await self.session.get(self.model, entity_id)


class QuotationComparisonRepository(BaseRepository[QuotationComparison]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(QuotationComparison, session)

    async def get_by_id(self, entity_id: int) -> Optional[QuotationComparison]:
        return await self.session.get(self.model, entity_id)

    async def get_by_rfq(self, rfq_id: int) -> Optional[QuotationComparison]:
        query = (
            select(self.model)
            .where(self.model.rfq_id == rfq_id)
            .options(
                selectinload(self.model.winner_technical),
                selectinload(self.model.winner_commercial),
                selectinload(self.model.final_selected_quotation)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
