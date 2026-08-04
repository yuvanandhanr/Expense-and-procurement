from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DeliveryItemCreate(BaseModel):
    po_item_id: int
    item_name: str
    quantity_shipped: int


class DeliveryItemSchema(DeliveryItemCreate):
    model_config = ConfigDict(from_attributes=True)

    delivery_item_id: int
    delivery_id: int


class DeliveryCreate(BaseModel):
    po_id: int
    vendor_id: int
    delivery_number: str
    expected_date: Optional[datetime] = None
    delivered_by: Optional[str] = None
    delivery_notes: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    items: List[DeliveryItemCreate]


class DeliveryUpdate(BaseModel):
    status: Optional[str] = None # Pending, Scheduled, In Transit, Delivered, Partially Delivered, Rejected, Returned, Completed
    delivery_date: Optional[datetime] = None
    delivered_by: Optional[str] = None
    delivery_notes: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None


class DeliverySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    delivery_id: int
    po_id: int
    vendor_id: int
    delivery_number: str
    delivery_date: Optional[datetime] = None
    expected_date: Optional[datetime] = None
    delivered_by: Optional[str] = None
    status: str
    delivery_notes: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[DeliveryItemSchema] = []
