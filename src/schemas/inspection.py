from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class InspectionItemCreate(BaseModel):
    delivery_item_id: int
    quantity_inspected: int
    quantity_accepted: int
    quantity_rejected: int
    serial_numbers: Optional[str] = None
    license_keys: Optional[str] = None
    notes: Optional[str] = None


class InspectionItemSchema(InspectionItemCreate):
    model_config = ConfigDict(from_attributes=True)

    inspection_item_id: int
    inspection_id: int


class InspectionCreate(BaseModel):
    delivery_id: int
    outcome: str # Accepted, Accepted with Remarks, Rejected, Partial Acceptance, Replacement Requested
    inspection_notes: Optional[str] = None
    damage_check_passed: Optional[bool] = True
    specification_check_passed: Optional[bool] = True
    quantity_verified: Optional[bool] = True
    items: List[InspectionItemCreate]


class InspectionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: int
    delivery_id: int
    inspected_by: Optional[int] = None
    inspection_date: datetime
    outcome: str
    inspection_notes: Optional[str] = None
    damage_check_passed: bool
    specification_check_passed: bool
    quantity_verified: bool
    created_at: datetime
    items: List[InspectionItemSchema] = []
