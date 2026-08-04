from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class InvoiceItemCreate(BaseModel):
    po_item_id: Optional[int] = None
    item_name: str
    quantity: int
    unit_price: Decimal


class InvoiceItemSchema(InvoiceItemCreate):
    model_config = ConfigDict(from_attributes=True)

    invoice_item_id: int
    invoice_id: int
    total_price: Decimal


class InvoiceDocumentCreate(BaseModel):
    file_name: str
    file_path: str


class InvoiceDocumentSchema(InvoiceDocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    invoice_id: int
    uploaded_at: datetime


class InvoiceApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: int
    invoice_id: int
    approver_id: Optional[int] = None
    status: str
    comments: Optional[str] = None
    actioned_at: datetime


class InvoiceCreate(BaseModel):
    invoice_number: str
    vendor_id: int
    po_id: Optional[int] = None
    grn_id: Optional[int] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: Optional[str] = "USD"
    taxes: Optional[Decimal] = Decimal("0.00")
    discount: Optional[Decimal] = Decimal("0.00")
    items: List[InvoiceItemCreate]


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None # Draft, Submitted, Validated, Approved, Rejected, Paid, Cancelled
    due_date: Optional[date] = None


class InvoiceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: int
    invoice_number: str
    vendor_id: int
    po_id: Optional[int] = None
    grn_id: Optional[int] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str
    subtotal: Decimal
    taxes: Decimal
    discount: Decimal
    grand_total: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItemSchema] = []
    documents: List[InvoiceDocumentSchema] = []
    approvals: List[InvoiceApprovalSchema] = []


class InvoiceApproveRequest(BaseModel):
    comments: Optional[str] = None
