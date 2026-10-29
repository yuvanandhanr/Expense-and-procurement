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


class InboxApprovalWorkflowSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workflow_id: int
    entity_type: str
    entity_id: int
    current_step_sequence: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    requestor_id: Optional[int] = None
    requestor_name: str
    requestor_role: Optional[str] = None
    requestor_department: Optional[str] = None
    title: Optional[str] = None
    justification: Optional[str] = None
    total_amount: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    past_approvers: List[str] = []
    steps: List[ApprovalStepSchema] = []
    can_approve: bool = False
    reason: Optional[str] = None
    incident_type: Optional[str] = None
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    serial_number: Optional[str] = None
    attachment_url: Optional[str] = None
    incident_date: Optional[str] = None
    manager_inspection_assessment: Optional[str] = None
    manager_inspection_comments: Optional[str] = None
    admin_inspection_resolution: Optional[str] = None
    admin_comments: Optional[str] = None
    linked_pr_id: Optional[int] = None



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
    physical_inspection_done: Optional[bool] = Field(False, description="Whether physical inspection was completed by Manager")


class PRRejectRequest(BaseModel):
    comments: str = Field(..., min_length=1, description="Required justification comments for rejection")


class PRReturnRequest(BaseModel):
    comments: str = Field(..., min_length=1, description="Required instructions explaining what modifications are needed")


class PRDelegateRequest(BaseModel):
    delegate_to_user_id: int = Field(..., description="Target user ID to delegate approval to")
    comments: Optional[str] = Field(None, description="Optional reason for delegation")


class PREscalateRequest(BaseModel):
    comments: Optional[str] = Field(None, description="Optional reason for escalation")
