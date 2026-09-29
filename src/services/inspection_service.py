from typing import List, Optional
from datetime import timezone, datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.inspection import InspectionReport, InspectionItem
from src.repositories.inspection import InspectionRepository, InspectionItemRepository
from src.repositories.delivery import DeliveryRepository
from src.schemas.inspection import InspectionCreate


class InspectionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.inspection_repo = InspectionRepository(db)
        self.item_repo = InspectionItemRepository(db)
        self.delivery_repo = DeliveryRepository(db)

    async def create_inspection(self, data: InspectionCreate, user_id: int) -> InspectionReport:
        delivery = await self.delivery_repo.get_by_id(data.delivery_id)
        if not delivery:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery record not found")

        # Validate outcome
        report = InspectionReport(
            delivery_id=data.delivery_id,
            inspected_by=user_id,
            inspection_date=datetime.utcnow(),
            outcome=data.outcome,
            inspection_notes=data.inspection_notes,
            damage_check_passed=data.damage_check_passed if data.damage_check_passed is not None else True,
            specification_check_passed=data.specification_check_passed if data.specification_check_passed is not None else True,
            quantity_verified=data.quantity_verified if data.quantity_verified is not None else True,
            created_at=datetime.utcnow()
        )
        report = await self.inspection_repo.create(report)

        for item_data in data.items:
            # Business Rule: license count / serial number validation
            if item_data.quantity_accepted + item_data.quantity_rejected != item_data.quantity_inspected:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Accepted quantity and rejected quantity must sum to inspected quantity"
                )

            item = InspectionItem(
                inspection_id=report.inspection_id,
                delivery_item_id=item_data.delivery_item_id,
                quantity_inspected=item_data.quantity_inspected,
                quantity_accepted=item_data.quantity_accepted,
                quantity_rejected=item_data.quantity_rejected,
                serial_numbers=item_data.serial_numbers,
                license_keys=item_data.license_keys,
                notes=item_data.notes
            )
            await self.item_repo.create(item)

        # Update delivery status based on outcome
        if data.outcome == "Accepted":
            delivery.status = "Delivered"
        elif data.outcome == "Rejected":
            delivery.status = "Rejected"
        elif data.outcome == "Partial Acceptance":
            delivery.status = "Partially Delivered"
        elif data.outcome == "Replacement Requested":
            delivery.status = "Returned"
        await self.delivery_repo.update(delivery)

        return await self.inspection_repo.get_by_id(report.inspection_id)
