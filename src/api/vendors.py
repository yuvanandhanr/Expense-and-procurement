from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User
from src.schemas.vendor import VendorCreate, VendorUpdate, VendorSchema, VendorDocumentSchema, VendorDocumentCreate, VendorContactCreate, VendorContactSchema
from src.services.vendor_service import VendorService

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def enforce_procurement_officer(current_user: User) -> None:
    """
    Restricts access to Procurement Officers, Procurement Managers, or Admins.
    """
    user_roles = [role.role_name for role in current_user.roles]
    allowed = ("Admin", "Procurement Officer", "Procurement Manager")
    if not any(role in allowed for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement officers or administrators are permitted to manage vendors"
        )


@router.post("", response_model=VendorSchema, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_procurement_officer(current_user)
    service = VendorService(db)
    return await service.create_vendor(data)


@router.get("", response_model=List[VendorSchema])
async def list_vendors(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = VendorService(db)
    return await service.vendor_repo.list_all()


@router.get("/{id}", response_model=VendorSchema)
async def get_vendor(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    service = VendorService(db)
    vendor = await service.vendor_repo.get_by_id(id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found")
    return vendor


@router.put("/{id}", response_model=VendorSchema)
async def update_vendor(
    id: int,
    data: VendorUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_procurement_officer(current_user)
    service = VendorService(db)
    return await service.update_vendor(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_procurement_officer(current_user)
    service = VendorService(db)
    # Check if vendor exists
    vendor = await service.vendor_repo.get_by_id(id)
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found")
    await service.vendor_repo.delete(id)


@router.post("/{id}/documents", response_model=VendorDocumentSchema, status_code=status.HTTP_201_CREATED)
async def upload_document(
    id: int,
    data: VendorDocumentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_procurement_officer(current_user)
    service = VendorService(db)
    return await service.upload_document(id, data.document_type, data.file_name, data.file_path)


@router.post("/{id}/contacts", response_model=VendorContactSchema, status_code=status.HTTP_201_CREATED)
async def add_contact(
    id: int,
    data: VendorContactCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    enforce_procurement_officer(current_user)
    service = VendorService(db)
    return await service.add_contact(id, data)


@router.post("/{id}/blacklist", response_model=VendorSchema)
async def blacklist_vendor(
    id: int,
    reason: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Blacklisting is restricted to Procurement Manager or Admin
    user_roles = [role.role_name for role in current_user.roles]
    if not any(role in ("Admin", "Procurement Manager") for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement managers or administrators are permitted to blacklist vendors"
        )
    service = VendorService(db)
    return await service.blacklist_vendor(id, reason, current_user.user_id)
