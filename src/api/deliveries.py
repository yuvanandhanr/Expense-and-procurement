from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.models.delivery import Delivery

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])

@router.get("")
async def get_deliveries(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Delivery)
    result = await session.execute(stmt)
    deliveries = result.scalars().all()
    
    mapped_deliveries = []
    for d in deliveries:
        mapped_deliveries.append({
            "delivery_id": d.delivery_id,
            "po_id": d.po_id,
            "delivery_number": d.delivery_number,
            "delivered_date": str(d.delivery_date) if d.delivery_date else "",
            "status": d.status
        })
        
    return mapped_deliveries
