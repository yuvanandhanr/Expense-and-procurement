from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class OffboardingTaskBase(BaseModel):
    task_type: str
    notes: Optional[str] = None

class OffboardingTaskCreate(OffboardingTaskBase):
    pass

class OffboardingTaskClear(BaseModel):
    notes: Optional[str] = None
    action: str = "Clear" # Clear, Reject, Pending Dues
    asset_condition: Optional[str] = None # Good, Damaged, Lost

class OffboardingTaskSchema(OffboardingTaskBase):
    model_config = ConfigDict(from_attributes=True)
    
    task_id: int
    employee_id: int
    asset_id: Optional[int] = None
    status: str
    cleared_by: Optional[int] = None
    cleared_at: Optional[datetime] = None
    created_at: datetime
