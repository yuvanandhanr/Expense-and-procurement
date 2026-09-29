from typing import List, Optional
from datetime import timezone, datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.vendor import (
    Vendor,
    VendorContact,
    VendorDocument,
    VendorCategory,
    VendorPerformance,
    VendorBlacklist,
)
from src.repositories.vendor import (
    VendorRepository,
    VendorContactRepository,
    VendorDocumentRepository,
    VendorCategoryRepository,
    VendorPerformanceRepository,
    VendorBlacklistRepository,
)
from src.schemas.vendor import VendorCreate, VendorUpdate, VendorContactCreate, VendorDocumentCreate


class VendorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.vendor_repo = VendorRepository(db)
        self.contact_repo = VendorContactRepository(db)
        self.doc_repo = VendorDocumentRepository(db)
        self.category_repo = VendorCategoryRepository(db)
        self.performance_repo = VendorPerformanceRepository(db)
        self.blacklist_repo = VendorBlacklistRepository(db)

    async def create_vendor(self, data: VendorCreate) -> Vendor:
        # Check duplicate code
        existing = await self.vendor_repo.get_by_code(data.vendor_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor with code '{data.vendor_code}' already exists"
            )

        vendor = Vendor(
            vendor_code=data.vendor_code,
            vendor_name=data.vendor_name,
            legal_name=data.legal_name,
            gst_vat_number=data.gst_vat_number,
            tax_number=data.tax_number,
            email=data.email,
            phone=data.phone,
            website=data.website,
            address=data.address,
            country=data.country,
            currency=data.currency or "USD",
            preferred_vendor=data.preferred_vendor or False,
            payment_terms=data.payment_terms,
            delivery_terms=data.delivery_terms,
            bank_details=data.bank_details,
            status="Active",
            blacklist_status=False
        )
        vendor = await self.vendor_repo.create(vendor)

        # Create Category tags
        for cat_name in (data.categories or []):
            cat = VendorCategory(vendor_id=vendor.vendor_id, category_name=cat_name)
            await self.category_repo.create(cat)

        # Initialize Performance metrics
        perf = VendorPerformance(vendor_id=vendor.vendor_id)
        await self.performance_repo.create(perf)

        return await self.vendor_repo.get_by_id(vendor.vendor_id)

    async def update_vendor(self, vendor_id: int, data: VendorUpdate) -> Vendor:
        vendor = await self.vendor_repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(vendor, k, v)
        
        vendor.updated_at = datetime.now(timezone.utc)
        await self.vendor_repo.update(vendor)
        return vendor

    async def upload_document(self, vendor_id: int, doc_type: str, file_name: str, file_path: str) -> VendorDocument:
        vendor = await self.vendor_repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

        doc = VendorDocument(
            vendor_id=vendor_id,
            document_type=doc_type,
            file_name=file_name,
            file_path=file_path,
            uploaded_at=datetime.now(timezone.utc)
        )
        return await self.doc_repo.create(doc)

    async def add_contact(self, vendor_id: int, data: VendorContactCreate) -> VendorContact:
        vendor = await self.vendor_repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

        contact = VendorContact(
            vendor_id=vendor_id,
            contact_name=data.contact_name,
            role=data.role,
            email=data.email,
            phone=data.phone
        )
        return await self.contact_repo.create(contact)

    async def blacklist_vendor(self, vendor_id: int, reason: str, user_id: int) -> Vendor:
        vendor = await self.vendor_repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

        vendor.blacklist_status = True
        vendor.status = "Inactive"
        await self.vendor_repo.update(vendor)

        blacklist_rec = VendorBlacklist(
            vendor_id=vendor_id,
            reason=reason,
            blacklisted_by=user_id,
            created_at=datetime.now(timezone.utc)
        )
        await self.blacklist_repo.create(blacklist_rec)

        return vendor
