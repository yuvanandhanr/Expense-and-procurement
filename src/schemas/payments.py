from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class PaymentApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: int
    payment_request_id: int
    approver_id: Optional[int] = None
    status: str
    comments: Optional[str] = None
    actioned_at: datetime


class PaymentRequestCreate(BaseModel):
    invoice_id: int
    po_id: Optional[int] = None
    amount: Decimal
    currency: Optional[str] = "USD"


class PaymentRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_request_id: int
    invoice_id: int
    po_id: Optional[int] = None
    request_number: str
    amount: Decimal
    currency: str
    status: str
    payment_readiness_passed: bool
    created_at: datetime
    approvals: List[PaymentApprovalSchema] = []


class PaymentApproveRequest(BaseModel):
    comments: Optional[str] = None
