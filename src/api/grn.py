from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.grn import GRNCreate, GRNSchema
from src.services.grn_service import GRNService
from src.repositories.grn import GRNRepository
from src.models.grn import GoodsReceipt

router = APIRouter(tags=["Goods Receipt Notes"])

@router.get("/grn", response_model=List[GRNSchema])
@router.get("/grns", response_model=List[GRNSchema])
async def list_grns(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = GRNRepository(session)
    return await repo.list_all(skip=skip, limit=limit)

@router.post("/grn", response_model=GRNSchema, status_code=status.HTTP_201_CREATED)
@router.post("/grns", response_model=GRNSchema, status_code=status.HTTP_201_CREATED)
async def create_grn(
    data: GRNCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    grn_service = GRNService(session)
    try:
        grn = await grn_service.create_grn(data, current_user.user_id)
        return grn
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
