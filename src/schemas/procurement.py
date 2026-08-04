from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProcurementClosureCreate(BaseModel):
    po_id: int
    audit_comments: Optional[str] = None


class ProcurementClosureSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    closure_id: int
    po_id: int
    closed_by: Optional[int] = None
    closed_at: datetime
    po_completed: bool
    grn_completed: bool
    invoice_approved: bool
    payment_approved: bool
    assets_registered: bool
    audit_comments: Optional[str] = None
