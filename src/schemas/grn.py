from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class GRNItemCreate(BaseModel):
    delivery_item_id: Optional[int] = None
    quantity_received: int
    quantity_rejected: int


class GRNItemSchema(GRNItemCreate):
    model_config = ConfigDict(from_attributes=True)

    grn_item_id: int
    grn_id: int


class GRNCreate(BaseModel):
    po_id: int
    vendor_id: int
    delivery_id: Optional[int] = None
    inspection_id: Optional[int] = None
    warehouse: Optional[str] = None
    notes: Optional[str] = None
    items: List[GRNItemCreate]


class GRNUpdate(BaseModel):
    status: Optional[str] = None # Pending, Partial, Completed, Rejected
    warehouse: Optional[str] = None
    notes: Optional[str] = None


class GRNSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grn_id: int
    grn_number: str
    po_id: Optional[int] = None
    vendor_id: Optional[int] = None
    delivery_id: Optional[int] = None
    inspection_id: Optional[int] = None
    warehouse: Optional[str] = None
    received_by: Optional[int] = None
    received_date: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    items: List[GRNItemSchema] = []
