from typing import List, Optional
from datetime import timezone, datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.delivery import Delivery, DeliveryItem
from src.repositories.delivery import DeliveryRepository, DeliveryItemRepository
from src.repositories.purchase_order import PORepository
from src.schemas.delivery import DeliveryCreate, DeliveryUpdate


class DeliveryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.delivery_repo = DeliveryRepository(db)
        self.item_repo = DeliveryItemRepository(db)
        self.po_repo = PORepository(db)

    async def create_delivery(self, data: DeliveryCreate) -> Delivery:
        # Check duplicate
        existing = await self.delivery_repo.get_by_number(data.delivery_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Delivery with number '{data.delivery_number}' already exists"
            )

        po = await self.po_repo.get_by_id(data.po_id)
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")

        delivery = Delivery(
            po_id=data.po_id,
            vendor_id=data.vendor_id,
            delivery_number=data.delivery_number,
            expected_date=data.expected_date,
            delivered_by=data.delivered_by,
            delivery_notes=data.delivery_notes,
            carrier=data.carrier,
            tracking_number=data.tracking_number,
            status="Pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        delivery = await self.delivery_repo.create(delivery)

        for item_data in data.items:
            item = DeliveryItem(
                delivery_id=delivery.delivery_id,
                po_item_id=item_data.po_item_id,
                item_name=item_data.item_name,
                quantity_shipped=item_data.quantity_shipped
            )
            await self.item_repo.create(item)

        # Update PO status to In Transit/Scheduled
        po.status = "In Transit"
        await self.po_repo.update(po)

        return await self.delivery_repo.get_by_id(delivery.delivery_id)

    async def update_delivery(self, delivery_id: int, data: DeliveryUpdate) -> Delivery:
        delivery = await self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(delivery, k, v)
        delivery.updated_at = datetime.utcnow()
        await self.delivery_repo.update(delivery)

        # Reconcile PO status based on delivery status
        po = await self.po_repo.get_by_id(delivery.po_id)
        if po:
            if delivery.status == "Delivered":
                po.status = "Delivered"
            elif delivery.status == "Partially Delivered":
                po.status = "Partially Delivered"
            elif delivery.status == "Rejected":
                po.status = "Delivery Rejected"
            await self.po_repo.update(po)

        return delivery
