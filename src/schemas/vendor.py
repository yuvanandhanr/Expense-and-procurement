from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class VendorContactBase(BaseModel):
    contact_name: str
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class VendorContactCreate(VendorContactBase):
    pass


class VendorContactSchema(VendorContactBase):
    model_config = ConfigDict(from_attributes=True)

    contact_id: int
    vendor_id: int
    created_at: datetime


class VendorDocumentBase(BaseModel):
    document_type: str
    file_name: str
    file_path: str


class VendorDocumentCreate(VendorDocumentBase):
    pass


class VendorDocumentSchema(VendorDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    vendor_id: int
    uploaded_at: datetime


class VendorCategoryBase(BaseModel):
    category_name: str


class VendorCategoryCreate(VendorCategoryBase):
    pass


class VendorCategorySchema(VendorCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    vendor_id: int
    created_at: datetime


class VendorPerformanceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    performance_id: int
    vendor_id: int
    delivery_performance: Decimal
    quality_score: Decimal
    response_time: Decimal
    contract_compliance: Decimal
    purchase_volume: Decimal
    avg_lead_time_days: Decimal
    rating: Decimal
    updated_at: datetime


class VendorBlacklistCreate(BaseModel):
    reason: str


class VendorBlacklistSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    blacklist_id: int
    vendor_id: int
    reason: str
    blacklisted_by: Optional[int] = None
    created_at: datetime


class VendorBase(BaseModel):
    vendor_code: str
    vendor_name: str
    legal_name: Optional[str] = None
    gst_vat_number: Optional[str] = None
    tax_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = "USD"
    preferred_vendor: Optional[bool] = False
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    bank_details: Optional[str] = None


class VendorCreate(VendorBase):
    categories: Optional[List[str]] = []


class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    legal_name: Optional[str] = None
    gst_vat_number: Optional[str] = None
    tax_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    preferred_vendor: Optional[bool] = None
    status: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    bank_details: Optional[str] = None


class VendorSchema(VendorBase):
    model_config = ConfigDict(from_attributes=True)

    vendor_id: int
    status: str
    blacklist_status: bool
    created_at: datetime
    updated_at: datetime
    contacts: List[VendorContactSchema] = []
    documents: List[VendorDocumentSchema] = []
    categories: List[VendorCategorySchema] = []
    performance: Optional[VendorPerformanceSchema] = None
