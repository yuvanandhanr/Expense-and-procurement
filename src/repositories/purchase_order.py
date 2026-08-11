from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POApproval
from src.repositories.base import BaseRepository


class PORepository(BaseRepository[PurchaseOrder]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PurchaseOrder, session)

    async def get_by_id(self, entity_id: int) -> Optional[PurchaseOrder]:
        query = (
            select(self.model)
            .where(self.model.po_id == entity_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.approvals)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_number(self, po_number: str) -> Optional[PurchaseOrder]:
        query = select(self.model).where(self.model.po_number == po_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_vendor(self, vendor_id: int) -> List[PurchaseOrder]:
        query = (
            select(self.model)
            .where(self.model.vendor_id == vendor_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.approvals)
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

class POItemRepository(BaseRepository[PurchaseOrderItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PurchaseOrderItem, session)

    async def get_by_id(self, entity_id: int) -> Optional[PurchaseOrderItem]:
        return await self.session.get(self.model, entity_id)


class POApprovalRepository(BaseRepository[POApproval]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(POApproval, session)

    async def get_by_id(self, entity_id: int) -> Optional[POApproval]:
        return await self.session.get(self.model, entity_id)

    async def get_active_approval_for_po(self, po_id: int) -> Optional[POApproval]:
        query = select(self.model).where(self.model.po_id == po_id, self.model.status == "Pending")
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
