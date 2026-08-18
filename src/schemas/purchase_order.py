from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class POItemCreate(BaseModel):
    item_name: str
    specification: Optional[str] = None
    quantity: int
    unit_price: Decimal


class POItemSchema(POItemCreate):
    model_config = ConfigDict(from_attributes=True)

    po_item_id: int
    po_id: int
    total_price: Decimal
    vendor_delivery_id: Optional[str] = None
    receiver_delivery_id: Optional[str] = None
    delivery_verification_status: Optional[str] = None


class ItemDeliveryRequest(BaseModel):
    vendor_product_id: str


class ItemVerificationRequest(BaseModel):
    receiver_product_id: str


class POApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: int
    po_id: int
    approver_id: int
    role_id: int
    status: str
    comments: Optional[str] = None
    actioned_at: Optional[datetime] = None


class POCreate(BaseModel):
    vendor_id: int
    rfq_id: Optional[int] = None
    pr_id: Optional[int] = None
    department_id: Optional[int] = None
    currency: Optional[str] = "USD"
    tax_amount: Optional[Decimal] = Decimal(0.00)
    discount_amount: Optional[Decimal] = Decimal(0.00)
    delivery_address: Optional[str] = None
    billing_address: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_date: Optional[datetime] = None
    items: List[POItemCreate]


class POUpdate(BaseModel):
    delivery_address: Optional[str] = None
    billing_address: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_date: Optional[datetime] = None
    status: Optional[str] = None


class POSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    po_id: int
    po_number: str
    vendor_id: int
    rfq_id: Optional[int] = None
    pr_id: Optional[int] = None
    department_id: Optional[int] = None
    total_amount: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    grand_total: Decimal
    delivery_address: Optional[str] = None
    billing_address: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_date: Optional[datetime] = None
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[POItemSchema] = []
    approvals: List[POApprovalSchema] = []


class POApproveRequest(BaseModel):
    comments: Optional[str] = None
