import uuid
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.rfq import RequestForQuotation, RFQItem, RFQVendor
from src.models.quotation import VendorQuotation, QuotationItem, QuotationComparison
from src.repositories.rfq import RFQRepository, RFQItemRepository, RFQVendorRepository
from src.repositories.quotation import QuotationRepository, QuotationItemRepository, QuotationComparisonRepository
from src.repositories.vendor import VendorRepository
from src.repositories.purchase_requisition import PRRepository
from src.schemas.rfq import RFQCreate, RFQUpdate
from src.schemas.quotation import QuotationCreate


class RFQService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.rfq_repo = RFQRepository(db)
        self.rfq_item_repo = RFQItemRepository(db)
        self.rfq_vendor_repo = RFQVendorRepository(db)
        self.quote_repo = QuotationRepository(db)
        self.quote_item_repo = QuotationItemRepository(db)
        self.comparison_repo = QuotationComparisonRepository(db)
        self.vendor_repo = VendorRepository(db)
        self.pr_repo = PRRepository(db)

    def generate_rfq_number(self) -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"RFQ-{date_str}-{rand_str}"

    def generate_quotation_number(self) -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"QT-{date_str}-{rand_str}"

    async def create_rfq(self, data: RFQCreate, user_id: int) -> RequestForQuotation:
        rfq = RequestForQuotation(
            rfq_number=self.generate_rfq_number(),
            pr_id=data.pr_id,
            title=data.title,
            description=data.description,
            status="Draft",
            submission_deadline=data.submission_deadline,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        rfq = await self.rfq_repo.create(rfq)

        # Create RFQ Items
        for item_data in data.items:
            item = RFQItem(
                rfq_id=rfq.rfq_id,
                pr_item_id=item_data.pr_item_id,
                item_name=item_data.item_name,
                specification=item_data.specification,
                quantity=item_data.quantity
            )
            await self.rfq_item_repo.create(item)

        # Invite vendors if provided
        for vendor_id in (data.invited_vendor_ids or []):
            await self.invite_vendor(rfq.rfq_id, vendor_id)

        return await self.rfq_repo.get_by_id(rfq.rfq_id)

    async def update_rfq(self, rfq_id: int, data: RFQUpdate) -> RequestForQuotation:
        rfq = await self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(rfq, k, v)
        
        rfq.updated_at = datetime.utcnow()
        await self.rfq_repo.update(rfq)
        return rfq

    async def publish_rfq(self, rfq_id: int) -> RequestForQuotation:
        rfq = await self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

        rfq.status = "Published"
        rfq.updated_at = datetime.utcnow()
        await self.rfq_repo.update(rfq)
        return rfq

    async def invite_vendor(self, rfq_id: int, vendor_id: int) -> RFQVendor:
        rfq = await self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

        vendor = await self.vendor_repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

        # Business Rule: Blacklisted vendors cannot receive RFQs!
        if vendor.blacklist_status or vendor.status == "Inactive":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor '{vendor.vendor_name}' is blacklisted/inactive and cannot be invited"
            )

        invite = RFQVendor(
            rfq_id=rfq_id,
            vendor_id=vendor_id,
            invited_at=datetime.utcnow()
        )
        return await self.rfq_vendor_repo.create(invite)

    async def submit_quotation(self, data: QuotationCreate) -> VendorQuotation:
        rfq = await self.rfq_repo.get_by_id(data.rfq_id)
        if not rfq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

        vendor = await self.vendor_repo.get_by_id(data.vendor_id)
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

        # Business Rule: Blacklisted vendors cannot submit quotes!
        if vendor.blacklist_status or vendor.status == "Inactive":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor '{vendor.vendor_name}' is blacklisted/inactive and cannot submit quotes"
            )

        # Calculate totals
        total_amount = Decimal("0.00")
        items_to_create = []

        for item_data in data.items:
            total_item_price = (item_data.unit_price * Decimal(1.00)) + item_data.tax_amount - item_data.discount_amount
            # Ensure price is valid
            total_amount += total_item_price
            
            q_item = QuotationItem(
                rfq_item_id=item_data.rfq_item_id,
                unit_price=item_data.unit_price,
                tax_amount=item_data.tax_amount,
                discount_amount=item_data.discount_amount,
                total_price=total_item_price
            )
            items_to_create.append(q_item)

        quote = VendorQuotation(
            quotation_number=self.generate_quotation_number(),
            rfq_id=data.rfq_id,
            vendor_id=data.vendor_id,
            total_amount=total_amount,
            currency=data.currency or "USD",
            lead_time_days=data.lead_time_days,
            warranty_months=data.warranty_months,
            technical_proposal=data.technical_proposal,
            commercial_proposal=data.commercial_proposal,
            technical_score=data.technical_score or Decimal("0.00"),
            commercial_score=data.commercial_score or Decimal("0.00"),
            status="Submitted",
            submitted_at=datetime.utcnow()
        )
        quote = await self.quote_repo.create(quote)

        # Associate and save quotation items
        for item in items_to_create:
            item.quotation_id = quote.quotation_id
            await self.quote_item_repo.create(item)

        # If RFQ was published, update status to Quotation Received
        if rfq.status == "Published":
            rfq.status = "Quotation Received"
            await self.rfq_repo.update(rfq)

        return await self.quote_repo.get_by_id(quote.quotation_id)

    async def get_comparison_matrix(self, rfq_id: int) -> QuotationComparison:
        """
        Retrieves or dynamically generates technical and commercial comparison metrics.
        """
        quotes = await self.quote_repo.list_by_rfq(rfq_id)
        if not quotes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No quotations submitted yet for comparison"
            )

        # Technical winner: Highest technical score
        # Commercial winner: Lowest total commercial amount
        winner_tech = max(quotes, key=lambda q: q.technical_score or Decimal("0.00"))
        winner_comm = min(quotes, key=lambda q: q.total_amount)

        # Locate existing matrix or build new draft comparison
        comp = await self.comparison_repo.get_by_rfq(rfq_id)
        if not comp:
            comp = QuotationComparison(
                rfq_id=rfq_id,
                winner_technical_quotation_id=winner_tech.quotation_id,
                winner_commercial_quotation_id=winner_comm.quotation_id,
                actioned_at=datetime.utcnow()
            )
            comp = await self.comparison_repo.create(comp)
        else:
            comp.winner_technical_quotation_id = winner_tech.quotation_id
            comp.winner_commercial_quotation_id = winner_comm.quotation_id
            comp.actioned_at = datetime.utcnow()
            await self.comparison_repo.update(comp)

        return await self.comparison_repo.get_by_id(comp.comparison_id)

    async def select_vendor(
        self,
        rfq_id: int,
        selected_vendor_id: int,
        selected_quotation_id: int,
        reason: str,
        user_id: int
    ) -> QuotationComparison:
        comp = await self.get_comparison_matrix(rfq_id)
        
        comp.final_selected_vendor_id = selected_vendor_id
        comp.final_selected_quotation_id = selected_quotation_id
        comp.selection_reason = reason
        comp.approved_by = user_id
        comp.actioned_at = datetime.utcnow()
        await self.comparison_repo.update(comp)

        # Update RFQ status to Closed
        rfq = await self.rfq_repo.get_by_id(rfq_id)
        rfq.status = "Closed"
        rfq.closing_date = datetime.utcnow()
        await self.rfq_repo.update(rfq)

        # Update quotation status
        quote = await self.quote_repo.get_by_id(selected_quotation_id)
        quote.status = "Selected"
        await self.quote_repo.update(quote)

        # Auto-generate Purchase Order
        from src.services.po_service import POService
        from src.schemas.purchase_order import POCreate, POItemCreate
        po_service = POService(self.db)
        
        po_items = []
        for item in quote.items:
            po_items.append(POItemCreate(
                item_name=item.rfq_item.item_name if item.rfq_item else "Item",
                specification=item.rfq_item.specification if item.rfq_item else None,
                quantity=item.rfq_item.quantity if item.rfq_item else 1,
                unit_price=item.unit_price
            ))
            
        pr_dept_id = None
        if rfq.pr_id:
            pr = await self.pr_repo.get_by_id(rfq.pr_id)
            if pr:
                pr_dept_id = pr.department_id

        po_data = POCreate(
            vendor_id=selected_vendor_id,
            rfq_id=rfq_id,
            pr_id=rfq.pr_id,
            department_id=pr_dept_id,
            currency=quote.currency,
            items=po_items
        )
        await po_service.create_po(po_data, user_id)

        return await self.comparison_repo.get_by_id(comp.comparison_id)
