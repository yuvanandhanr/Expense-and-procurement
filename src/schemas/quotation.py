from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class QuotationItemCreate(BaseModel):
    rfq_item_id: int
    unit_price: Decimal
    tax_amount: Optional[Decimal] = Decimal(0.00)
    discount_amount: Optional[Decimal] = Decimal(0.00)


class QuotationItemSchema(QuotationItemCreate):
    model_config = ConfigDict(from_attributes=True)

    quotation_item_id: int
    quotation_id: int
    total_price: Decimal


class QuotationCreate(BaseModel):
    rfq_id: int
    vendor_id: int
    currency: Optional[str] = "USD"
    lead_time_days: Optional[int] = None
    warranty_months: Optional[int] = None
    technical_proposal: Optional[str] = None
    commercial_proposal: Optional[str] = None
    technical_score: Optional[Decimal] = None
    commercial_score: Optional[Decimal] = None
    items: List[QuotationItemCreate]


class QuotationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quotation_id: int
    quotation_number: str
    rfq_id: int
    vendor_id: int
    total_amount: Decimal
    currency: str
    lead_time_days: Optional[int] = None
    warranty_months: Optional[int] = None
    technical_proposal: Optional[str] = None
    commercial_proposal: Optional[str] = None
    technical_score: Optional[Decimal] = None
    commercial_score: Optional[Decimal] = None
    status: str
    submitted_at: datetime
    items: List[QuotationItemSchema] = []


class ComparisonMatrixSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comparison_id: int
    rfq_id: int
    winner_technical_quotation_id: Optional[int] = None
    winner_commercial_quotation_id: Optional[int] = None
    final_selected_vendor_id: Optional[int] = None
    final_selected_quotation_id: Optional[int] = None
    selection_reason: Optional[str] = None
    approved_by: Optional[int] = None
    actioned_at: datetime


class VendorSelectionRequest(BaseModel):
    selected_vendor_id: int
    selected_quotation_id: int
    reason: str
