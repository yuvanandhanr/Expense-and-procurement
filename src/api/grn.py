from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.grn import GRNCreate, GRNSchema
from src.services.grn_service import GRNService
from src.models.grn import GoodsReceipt

router = APIRouter(prefix="/grn", tags=["Goods Receipt Notes"])

@router.post("", response_model=GRNSchema, status_code=status.HTTP_201_CREATED)
async def create_grn(
    data: GRNCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    grn_service = GRNService(session)
    try:
        grn = await grn_service.create_grn(data, current_user.user_id)
        # We need to refresh or return appropriately. Assuming create_grn flushes and it has an id.
        return grn
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
