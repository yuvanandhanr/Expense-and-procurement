from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.purchase_order import POCreate, POUpdate, POSchema, POApproveRequest, ItemDeliveryRequest, ItemVerificationRequest, POItemSchema
from src.services.po_service import POService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


def enforce_po_access(current_user: User) -> None:
    user_roles = [role.role_name for role in current_user.roles]
    allowed = ("Admin", "Procurement Officer", "Procurement Manager", "Finance", "Finance Manager", "CFO", "Vendor Portal", "Employee", "Manager")
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
            # Vendors should not see Draft POs
            pos = await service.po_repo.list_by_vendor(vendor_id)
            return [po for po in pos if po.status != "Draft"]
        return []

    # If the user is just an Employee or Manager, restrict to their PRs
    # (Assuming Procurement, Admin, Finance, CFO can see all POs)
    has_global_access = any(role in ("Admin", "Procurement Officer", "Procurement Manager", "Finance", "Finance Manager", "CFO") for role in user_roles)
    if not has_global_access:
        return await service.po_repo.list_by_requestor(current_user.user_id)

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


@router.post("/{id}/items/{item_id}/vendor-deliver", response_model=POItemSchema)
async def vendor_deliver_item(
    id: int,
    item_id: int,
    data: ItemDeliveryRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_po_access(current_user)
    # Require Vendor Portal role
    user_roles = [role.role_name for role in current_user.roles]
    if "Vendor Portal" not in user_roles and not any(role in ("Admin",) for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can mark items as delivered"
        )
    
    service = POService(db)
    return await service.mark_item_delivered_by_vendor(id, item_id, data.vendor_product_id)


@router.post("/{id}/items/{item_id}/verify-delivery", response_model=POItemSchema)
async def verify_item_delivery(
    id: int,
    item_id: int,
    data: ItemVerificationRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_po_access(current_user)
    # Require Internal Employee roles
    user_roles = [role.role_name for role in current_user.roles]
    if "Vendor Portal" in user_roles and not any(role in ("Admin", "Employee", "Procurement Officer") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendors cannot verify their own delivery"
        )
    
    service = POService(db)
    return await service.verify_item_delivery(id, item_id, data.receiver_product_id, current_user.user_id)
