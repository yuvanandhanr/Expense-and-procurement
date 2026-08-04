from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.payments import PaymentRequest, PaymentApproval
from src.repositories.base import BaseRepository


class PaymentRequestRepository(BaseRepository[PaymentRequest]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PaymentRequest, session)

    async def get_by_id(self, entity_id: int) -> Optional[PaymentRequest]:
        query = (
            select(self.model)
            .where(self.model.payment_request_id == entity_id)
            .options(
                selectinload(self.model.approvals),
                selectinload(self.model.invoice)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, request_number: str) -> Optional[PaymentRequest]:
        query = select(self.model).where(self.model.request_number == request_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_invoice(self, invoice_id: int) -> Optional[PaymentRequest]:
        query = select(self.model).where(self.model.invoice_id == invoice_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class PaymentApprovalRepository(BaseRepository[PaymentApproval]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PaymentApproval, session)

    async def get_by_id(self, entity_id: int) -> Optional[PaymentApproval]:
        return await self.session.get(self.model, entity_id)
