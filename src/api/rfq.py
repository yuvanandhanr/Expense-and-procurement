from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.rfq import RFQCreate, RFQUpdate, RFQSchema, RFQVendorSchema
from src.schemas.quotation import ComparisonMatrixSchema, VendorSelectionRequest
from src.services.rfq_service import RFQService

router = APIRouter(prefix="/rfq", tags=["RFQ Management"])


def enforce_procurement_officer_or_creator(rfq, current_user: User) -> None:
    user_roles = [role.role_name for role in current_user.roles]
    if "Admin" in user_roles or "Procurement Officer" in user_roles or "Procurement Manager" in user_roles:
        return
    
    if rfq.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are restricted to accessing your own RFQs only"
        )


@router.post("", response_model=RFQSchema, status_code=status.HTTP_201_CREATED)
async def create_rfq(
    data: RFQCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Restrict creation to Procurement Officers, Managers, or Admin
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Officer", "Procurement Manager") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement officers or administrators are permitted to create RFQs"
        )
    service = RFQService(db)
    return await service.create_rfq(data, current_user.user_id)


@router.get("", response_model=List[RFQSchema])
async def list_rfqs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = RFQService(db)
    user_roles = [role.role_name for role in current_user.roles]

    if any(role in ("Admin", "Procurement Officer", "Procurement Manager") for role in user_roles):
        return await service.rfq_repo.list_all()
    elif "Vendor Portal" in user_roles:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from src.models.vendor import Vendor
        from src.models.rfq import RFQVendor
        
        # Get vendor ID
        stmt = select(Vendor.vendor_id).where(Vendor.email == current_user.email)
        result = await db.execute(stmt)
        vendor_id = result.scalar_one_or_none()
        
        if vendor_id:
            # Get RFQs where this vendor is invited
            query = (
                select(service.rfq_repo.model)
                .join(RFQVendor, RFQVendor.rfq_id == service.rfq_repo.model.rfq_id)
                .where(RFQVendor.vendor_id == vendor_id)
                .options(
                    selectinload(service.rfq_repo.model.items),
                    selectinload(service.rfq_repo.model.rfq_vendors),
                    selectinload(service.rfq_repo.model.quotations)
                )
            )
            result = await db.execute(query)
            return list(result.scalars().all())
        return []
    else:
        # Employees see only RFQs they created
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        query = (
            select(service.rfq_repo.model)
            .where(service.rfq_repo.model.created_by == current_user.user_id)
            .options(
                selectinload(service.rfq_repo.model.items),
                selectinload(service.rfq_repo.model.rfq_vendors),
                selectinload(service.rfq_repo.model.quotations)
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())


@router.get("/{id}", response_model=RFQSchema)
async def get_rfq(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = RFQService(db)
    rfq = await service.rfq_repo.get_by_id(id)
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

    enforce_procurement_officer_or_creator(rfq, current_user)
    return rfq


@router.put("/{id}", response_model=RFQSchema)
async def update_rfq(
    id: int,
    data: RFQUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = RFQService(db)
    rfq = await service.rfq_repo.get_by_id(id)
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

    enforce_procurement_officer_or_creator(rfq, current_user)
    return await service.update_rfq(id, data)


@router.post("/{id}/publish", response_model=RFQSchema)
async def publish_rfq(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = RFQService(db)
    rfq = await service.rfq_repo.get_by_id(id)
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

    enforce_procurement_officer_or_creator(rfq, current_user)
    return await service.publish_rfq(id)


@router.post("/{id}/invite", response_model=RFQVendorSchema, status_code=status.HTTP_201_CREATED)
async def invite_vendor(
    id: int,
    vendor_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = RFQService(db)
    rfq = await service.rfq_repo.get_by_id(id)
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

    enforce_procurement_officer_or_creator(rfq, current_user)
    return await service.invite_vendor(id, vendor_id)


@router.get("/{id}/comparison", response_model=ComparisonMatrixSchema)
async def get_comparison(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Quote evaluation restricted to Procurement Officer, Procurement Manager, or Admin
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Officer", "Procurement Manager", "Finance Manager", "CFO") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement officers or managers are permitted to evaluate quotations"
        )
    service = RFQService(db)
    return await service.get_comparison_matrix(id)


@router.post("/{id}/select-vendor", response_model=ComparisonMatrixSchema)
async def select_vendor(
    id: int,
    data: VendorSelectionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Vendor Selection Approval is restricted to Finance Manager, CFO, Procurement Manager, or Admin
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Manager", "Finance Manager", "Finance", "CFO") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only finance, CFO, procurement managers, or administrators are permitted to approve vendor selections"
        )
    service = RFQService(db)
    return await service.select_vendor(
        id,
        data.selected_vendor_id,
        data.selected_quotation_id,
        data.reason,
        current_user.user_id
    )
