from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.purchase_order import POCreate, POUpdate, POSchema, POApproveRequest
from src.services.po_service import POService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


def enforce_po_access(current_user: User) -> None:
    user_roles = [role.role_name for role in current_user.roles]
    allowed = ("Admin", "Procurement Officer", "Procurement Manager", "Finance", "CFO", "Vendor Portal")
    if not any(role in allowed for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not possess the authorization permissions required to view or manage Purchase Orders"
        )


@router.post("", response_model=POSchema, status_code=status.HTTP_201_CREATED)
async def create_po(
    data: POCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_po_access(current_user)
    # Only Procurement Officer, Procurement Manager, or Admin can create POs
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Officer", "Procurement Manager") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement officers or managers are permitted to generate Purchase Orders"
        )
    service = POService(db)
    return await service.create_po(data, current_user.user_id)


@router.get("", response_model=List[POSchema])
async def list_pos(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_po_access(current_user)
    service = POService(db)
    user_roles = [role.role_name for role in current_user.roles]
    
    if "Vendor Portal" in user_roles and not any(role in ("Admin", "Procurement Officer", "Procurement Manager", "Finance", "CFO") for role in user_roles):
        from sqlalchemy import select
        from src.models.vendor import Vendor
        stmt = select(Vendor.vendor_id).where(Vendor.email == current_user.email)
        result = await db.execute(stmt)
        vendor_id = result.scalar_one_or_none()
        if vendor_id:
            # list_by_vendor needs to exist in po_repo
            return await service.po_repo.list_by_vendor(vendor_id)
        return []

    return await service.po_repo.list_all()


@router.get("/{id}", response_model=POSchema)
async def get_po(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_po_access(current_user)
    service = POService(db)
    po = await service.po_repo.get_by_id(id)
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Order not found")
        
    user_roles = [role.role_name for role in current_user.roles]
    if "Vendor Portal" in user_roles and not any(role in ("Admin", "Procurement Officer", "Procurement Manager", "Finance", "CFO") for role in user_roles):
        from sqlalchemy import select
        from src.models.vendor import Vendor
        stmt = select(Vendor.vendor_id).where(Vendor.email == current_user.email)
        result = await db.execute(stmt)
        vendor_id = result.scalar_one_or_none()
        if po.vendor_id != vendor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only access your own Purchase Orders")
            
    return po


@router.put("/{id}", response_model=POSchema)
async def update_po(
    id: int,
    data: POUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_po_access(current_user)
    service = POService(db)
    return await service.update_po(id, data)


@router.post("/{id}/approve", response_model=POSchema)
async def approve_po(
    id: int,
    data: POApproveRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # PO Approval is restricted to Procurement Manager, CFO, or Admin
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Manager", "CFO") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement managers, CFOs, or administrators are permitted to approve Purchase Orders"
        )

    # Determine highest role_id the current user holds
    # Let's say Procurement Manager is role_id 2 or 3, Admin is 4.
    # We can default to role_id=2 or 4.
    role_id = 2
    if "Admin" in user_roles:
        role_id = 4
    elif "CFO" in user_roles:
        role_id = 4

    service = POService(db)
    return await service.approve_po(id, current_user.user_id, role_id, data.comments)


@router.post("/{id}/issue", response_model=POSchema)
async def issue_po(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # PO Issuing restricted to Procurement Officers or Admins
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Officer", "Procurement Manager") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement officers or managers are permitted to issue Purchase Orders"
        )
    service = POService(db)
    return await service.issue_po(id)
