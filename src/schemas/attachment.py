from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PRAttachmentBase(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    file_size: int


class PRAttachmentCreate(PRAttachmentBase):
    pass


class PRAttachmentSchema(PRAttachmentBase):
    model_config = ConfigDict(from_attributes=True)

    attachment_id: int
    pr_id: int
    uploaded_by: Optional[int] = None
    created_at: datetime
