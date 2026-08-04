from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class AssetCategoryCreate(BaseModel):
    category_name: str
    description: Optional[str] = None


class AssetCategorySchema(AssetCategoryCreate):
    model_config = ConfigDict(from_attributes=True)

    category_id: int


class AssetAssignmentCreate(BaseModel):
    assigned_to: int
    assigned_date: date
    notes: Optional[str] = None


class AssetAssignmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: int
    asset_id: int
    assigned_to: Optional[int] = None
    assigned_by: Optional[int] = None
    assigned_date: date
    return_date: Optional[date] = None
    status: str
    notes: Optional[str] = None


class AssetTransferRequest(BaseModel):
    transfer_to_employee_id: int
    notes: Optional[str] = None


class AssetReturnRequest(BaseModel):
    return_date: date
    notes: Optional[str] = None


class AssetHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    asset_id: int
    action_type: str
    action_by: Optional[int] = None
    action_date: datetime
    details: Optional[str] = None


class AssetDocumentCreate(BaseModel):
    document_type: str
    file_name: str
    file_path: str


class AssetDocumentSchema(AssetDocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    asset_id: int
    uploaded_at: datetime


class AssetCreate(BaseModel):
    asset_number: str
    asset_tag: str
    category_id: Optional[int] = None
    po_id: Optional[int] = None
    vendor_id: Optional[int] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    department_id: Optional[int] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    amc_expiry: Optional[date] = None
    location: Optional[str] = None


class AssetUpdate(BaseModel):
    status: Optional[str] = None # Available, Assigned, Under Maintenance, Disposed, Returned, Lost
    location: Optional[str] = None
    warranty_expiry: Optional[date] = None
    amc_expiry: Optional[date] = None


class AssetSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    asset_number: str
    asset_tag: str
    category_id: Optional[int] = None
    po_id: Optional[int] = None
    vendor_id: Optional[int] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    department_id: Optional[int] = None
    assigned_employee_id: Optional[int] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    amc_expiry: Optional[date] = None
    location: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    assignments: List[AssetAssignmentSchema] = []
    history: List[AssetHistorySchema] = []
    documents: List[AssetDocumentSchema] = []
