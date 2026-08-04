from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RFQItemCreate(BaseModel):
    pr_item_id: Optional[int] = None
    item_name: str
    specification: Optional[str] = None
    quantity: int


class RFQItemSchema(RFQItemCreate):
    model_config = ConfigDict(from_attributes=True)

    rfq_item_id: int
    rfq_id: int


class RFQVendorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rfq_vendor_id: int
    rfq_id: int
    vendor_id: int
    invited_at: datetime


class RFQCreate(BaseModel):
    title: str
    description: Optional[str] = None
    pr_id: Optional[int] = None
    submission_deadline: Optional[datetime] = None
    invited_vendor_ids: Optional[List[int]] = []
    items: List[RFQItemCreate] = []


class RFQUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    submission_deadline: Optional[datetime] = None
    status: Optional[str] = None


class RFQSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rfq_id: int
    rfq_number: str
    pr_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str
    submission_deadline: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[RFQItemSchema] = []
    rfq_vendors: List[RFQVendorSchema] = []
