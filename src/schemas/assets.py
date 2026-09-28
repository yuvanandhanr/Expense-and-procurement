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
    status: Optional[str] = None
    po_id: Optional[int] = None
    vendor_id: Optional[int] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    department_id: Optional[int] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    amc_expiry: Optional[date] = None
    cost: Optional[float] = None
    location: Optional[str] = None
    cost: Optional[float] = None


class AssetUpdate(BaseModel):
    status: Optional[str] = None
    model: Optional[str] = None
    category_id: Optional[int] = None
    location: Optional[str] = None
    cost: Optional[float] = None
    warranty_expiry: Optional[date] = None
    amc_expiry: Optional[date] = None
    cost: Optional[float] = None


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
    cost: Optional[float] = None
    location: Optional[str] = None
    cost: Optional[float] = None
    cost: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime
    assignments: List[AssetAssignmentSchema] = []
    history: List[AssetHistorySchema] = []
    documents: List[AssetDocumentSchema] = []


class AssetIncidentCreate(BaseModel):
    asset_id: int
    description: str
    incident_type: str
    image_url: Optional[str] = None
    is_draft: Optional[bool] = False
    department_name: Optional[str] = None
    employee_type: Optional[str] = None


class AssetIncidentUpdate(BaseModel):
    description: Optional[str] = None
    incident_type: Optional[str] = None
    image_url: Optional[str] = None


class AssetIncidentAction(BaseModel):
    action: str # Approve, Reject, Return for Correction
    resolution: Optional[str] = None
    manager_inspection_assessment: Optional[str] = None
    manager_inspection_comments: Optional[str] = None
    admin_inspection_resolution: Optional[str] = None
    admin_comments: Optional[str] = None


class AssetIncidentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: Optional[int] = None
    asset_id: int
    reporter_id: Optional[int] = None
    description: str
    incident_date: Optional[date] = None
    incident_type: str
    status: str
    resolution: Optional[str] = None
    image_url: Optional[str] = None
    physical_inspection_done: Optional[bool] = False
    manager_inspection_assessment: Optional[str] = None
    manager_inspection_comments: Optional[str] = None
    admin_inspection_resolution: Optional[str] = None
    admin_comments: Optional[str] = None
    linked_pr_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
