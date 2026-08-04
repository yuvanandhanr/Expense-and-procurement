from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ApprovalMatrixBase(BaseModel):
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    purchase_type: Optional[str] = None
    min_amount: Decimal = Field(default=0.00, ge=0)
    max_amount: Decimal = Field(default=99999999.99, ge=0)
    approval_level: int = Field(..., ge=1)
    role_id: int = Field(..., description="Role responsible for approving at this level")


class ApprovalMatrixCreate(ApprovalMatrixBase):
    pass


class ApprovalMatrixSchema(ApprovalMatrixBase):
    model_config = ConfigDict(from_attributes=True)

    matrix_id: int
    created_at: datetime
    updated_at: datetime


class ApprovalStepSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_id: int
    workflow_id: Optional[int] = None
    step_number: int
    approver_role_id: Optional[int] = None
    approver_id: Optional[int] = None
    status: str
    actioned_at: Optional[datetime] = None


class ApprovalWorkflowSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workflow_id: int
    pr_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    steps: List[ApprovalStepSchema] = []


class WorkflowHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    pr_id: Optional[int] = None
    action: str
    performed_by: Optional[int] = None
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime


class ApprovalHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    step_id: Optional[int] = None
    action: str
    performed_by: Optional[int] = None
    comments: Optional[str] = None
    created_at: datetime


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, description="Text body of the comment")
    parent_comment_id: Optional[int] = Field(None, description="Parent comment ID for nesting")
    is_internal: Optional[bool] = Field(False, description="Flag for internal review notes")


class CommentCreate(CommentBase):
    pass


class CommentSchema(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    pr_id: Optional[int] = None
    user_id: int
    created_at: datetime
    replies: List["CommentSchema"] = []


# Actions Payload Schemas
class PRApproveRequest(BaseModel):
    comments: Optional[str] = Field(None, description="Optional approval comments")


class PRRejectRequest(BaseModel):
    comments: str = Field(..., min_length=1, description="Required justification comments for rejection")


class PRReturnRequest(BaseModel):
    comments: str = Field(..., min_length=1, description="Required instructions explaining what modifications are needed")


class PRDelegateRequest(BaseModel):
    delegate_to_user_id: int = Field(..., description="Target user ID to delegate approval to")
    comments: Optional[str] = Field(None, description="Optional reason for delegation")


class PREscalateRequest(BaseModel):
    comments: Optional[str] = Field(None, description="Optional reason for escalation")
