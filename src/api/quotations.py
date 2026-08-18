from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.quotation import QuotationCreate, QuotationSchema
from src.services.rfq_service import RFQService

router = APIRouter(prefix="/quotations", tags=["Quotation Management"])


@router.post("", response_model=QuotationSchema, status_code=status.HTTP_201_CREATED)
async def submit_quotation(
    data: QuotationCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Quote submission is open to invited vendors, coordinated by Procurement Officers or Admin
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Officer", "Procurement Manager", "Vendor Portal") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement personnel, administrators, or vendors can log quotation submissions"
        )
    
    if "Vendor Portal" in user_roles and not any(role in ("Admin", "Procurement Officer", "Procurement Manager") for role in user_roles):
        from sqlalchemy import select
        from src.models.vendor import Vendor
        stmt = select(Vendor.vendor_id).where(Vendor.email == current_user.email)
        result = await db.execute(stmt)
        vendor_id = result.scalar_one_or_none()
        if not vendor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor record not found for this user")
        
        # Enforce that vendors can only submit quotations for themselves
        if data.vendor_id != vendor_id:
            data.vendor_id = vendor_id
    service = RFQService(db)
    return await service.submit_quotation(data)


@router.get("", response_model=List[QuotationSchema])
async def list_quotations(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = RFQService(db)
    user_roles = [role.role_name for role in current_user.roles]
    
    if any(role in ("Admin", "Procurement Officer", "Procurement Manager", "Finance Manager", "Finance", "CFO", "Manager") for role in user_roles):
        return await service.quote_repo.list_all()
    elif "Vendor Portal" in user_roles:
        from sqlalchemy import select
        from src.models.vendor import Vendor
        stmt = select(Vendor.vendor_id).where(Vendor.email == current_user.email)
        result = await db.execute(stmt)
        vendor_id = result.scalar_one_or_none()
        if vendor_id:
            return await service.quote_repo.list_by_vendor(vendor_id)
        return []
    
    return []
