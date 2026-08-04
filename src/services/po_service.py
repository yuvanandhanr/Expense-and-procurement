import uuid
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POApproval
from src.models.contract import Contract
from src.repositories.purchase_order import PORepository, POItemRepository, POApprovalRepository
from src.repositories.quotation import QuotationRepository
from src.repositories.purchase_requisition import PRRepository
from src.repositories.contract import ContractRepository, RateContractRepository
from src.schemas.purchase_order import POCreate, POUpdate


class POService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.po_repo = PORepository(db)
        self.po_item_repo = POItemRepository(db)
        self.po_approval_repo = POApprovalRepository(db)
        self.quote_repo = QuotationRepository(db)
        self.pr_repo = PRRepository(db)
        self.contract_repo = ContractRepository(db)
        self.rate_contract_repo = RateContractRepository(db)

    def generate_po_number(self) -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"PO-{date_str}-{rand_str}"

    async def create_po(self, data: POCreate, user_id: int) -> PurchaseOrder:
        # Check Contract status if provided
        # Let's see if any active contract exists
        # Business Rule: Expired contracts cannot generate Purchase Orders!
        # Find if there is a contract linked to the vendor
        from sqlalchemy import select
        query = select(Contract).where(Contract.vendor_id == data.vendor_id, Contract.status == "Expired")
        result = await self.db.execute(query)
        expired_contract = result.scalar_one_or_none()
        if expired_contract:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor contract '{expired_contract.contract_number}' is expired. Cannot create Purchase Order."
            )

        # Business Rule: High-value purchases (> $10,000) require minimum three vendor quotations,
        # unless an existing rate contract is bypass-valid.
        pr_total = Decimal("0.00")
        has_rate_contract = True

        if data.pr_id:
            pr = await self.pr_repo.get_by_id(data.pr_id)
            if pr:
                pr_total = pr.total_estimated_amount

                # Check if rate contract exists for all items
                for item in pr.items:
                    rate_c = await self.rate_contract_repo.find_rate_contract_for_item(item.item_name)
                    if not rate_c:
                        has_rate_contract = False
                        break
            else:
                has_rate_contract = False
        else:
            has_rate_contract = False

        # Calculate Grand Total of PO
        total_amt = sum(item.unit_price * item.quantity for item in data.items)
        grand_total = total_amt + data.tax_amount - data.discount_amount

        # Check high-value quotes requirement
        if grand_total > Decimal("10000.00") and not has_rate_contract:
            if data.rfq_id:
                quotes = await self.quote_repo.list_by_rfq(data.rfq_id)
                if len(quotes) < 3:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"High-value purchase exceeds $10,000 and requires at least 3 vendor quotations. Currently submitted: {len(quotes)}"
                    )
            elif pr_total > Decimal("10000.00"):
                # Missing RFQ completely on high-value
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="High-value purchase exceeds $10,000 and requires RFQ with at least 3 vendor quotations."
                )

        po = PurchaseOrder(
            po_number=self.generate_po_number(),
            vendor_id=data.vendor_id,
            rfq_id=data.rfq_id,
            pr_id=data.pr_id,
            department_id=data.department_id,
            total_amount=total_amt,
            tax_amount=data.tax_amount,
            discount_amount=data.discount_amount,
            grand_total=grand_total,
            delivery_address=data.delivery_address,
            billing_address=data.billing_address,
            payment_terms=data.payment_terms,
            delivery_date=data.delivery_date,
            status="Draft",
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        po = await self.po_repo.create(po)

        # Create PO Items
        for item_data in data.items:
            item = PurchaseOrderItem(
                po_id=po.po_id,
                item_name=item_data.item_name,
                specification=item_data.specification,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total_price=item_data.unit_price * item_data.quantity
            )
            await self.po_item_repo.create(item)

        return await self.po_repo.get_by_id(po.po_id)

    async def update_po(self, po_id: int, data: POUpdate) -> PurchaseOrder:
        po = await self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(po, k, v)

        po.updated_at = datetime.utcnow()
        await self.po_repo.update(po)
        return po

    async def approve_po(self, po_id: int, user_id: int, role_id: int, comments: Optional[str] = None) -> PurchaseOrder:
        po = await self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")

        # Business Rule: Procurement Manager approval required. High-value PO (> $50,000) requires CFO approval.
        # CFO role_id fallback is mapped dynamically (e.g. role_id = 4).
        # We record the approval step
        approval = POApproval(
            po_id=po_id,
            approver_id=user_id,
            role_id=role_id,
            status="Approved",
            comments=comments or "Approved",
            actioned_at=datetime.utcnow()
        )
        await self.po_approval_repo.create(approval)

        # Check high-value threshold to finalise PO status
        if po.grand_total > Decimal("50000.00"):
            # Check if CFO (role_id=4 or dynamic CFO role) has approved
            # If the current approver is CFO, we mark PO Approved
            if role_id == 4:
                po.status = "Approved"
            else:
                po.status = "Pending CFO Approval"
        else:
            # Standard PO approved by Procurement Manager (role_id=2 or 4)
            po.status = "Approved"

        await self.po_repo.update(po)
        return await self.po_repo.get_by_id(po_id)

    async def issue_po(self, po_id: int) -> PurchaseOrder:
        po = await self.po_repo.get_by_id(po_id)
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PO not found")

        if po.status != "Approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only fully approved Purchase Orders can be issued. Current status: {po.status}"
            )

        po.status = "Issued"
        await self.po_repo.update(po)
        return po
