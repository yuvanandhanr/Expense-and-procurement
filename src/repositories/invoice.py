from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.invoice import VendorInvoice, InvoiceItem, InvoiceApproval, InvoiceDocument
from src.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[VendorInvoice]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(VendorInvoice, session)

    async def get_by_id(self, entity_id: int) -> Optional[VendorInvoice]:
        query = (
            select(self.model)
            .where(self.model.invoice_id == entity_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.documents),
                selectinload(self.model.approvals),
                selectinload(self.model.po)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_vendor_and_number(self, vendor_id: int, invoice_number: str) -> Optional[VendorInvoice]:
        query = select(self.model).where(self.model.vendor_id == vendor_id, self.model.invoice_number == invoice_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class InvoiceItemRepository(BaseRepository[InvoiceItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InvoiceItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[InvoiceItem]:
        return await self.session.get(self.model, entity_id)


class InvoiceDocumentRepository(BaseRepository[InvoiceDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InvoiceDocument, session)

    async def get_by_id(self, entity_id: int) -> Optional[InvoiceDocument]:
        return await self.session.get(self.model, entity_id)


class InvoiceApprovalRepository(BaseRepository[InvoiceApproval]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InvoiceApproval, session)

    async def get_by_id(self, entity_id: int) -> Optional[InvoiceApproval]:
        return await self.session.get(self.model, entity_id)
