from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal

# Receipt Schemas
class ReceiptBase(BaseModel):
    merchant_name: Optional[str] = None
    receipt_date: Optional[date] = None
    category: Optional[str] = None
    verified_amount: Decimal = Field(default=Decimal("0.00"))
    tax: Decimal = Field(default=Decimal("0.00"))
    currency: str = "USD"

class ReceiptCreate(ReceiptBase):
    pass

class ReceiptUpdate(ReceiptBase):
    pass

class ReceiptResponse(ReceiptBase):
    receipt_id: int
    expense_report_id: int
    ocr_amount: Decimal
    ocr_confidence: Optional[Decimal]
    image_path: str
    file_name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Expense Report Schemas
class ExpenseReportBase(BaseModel):
    purpose: str
    justification: Optional[str] = None
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    project_code: Optional[str] = None
    currency: str = "USD"

class ExpenseReportCreate(ExpenseReportBase):
    pass

class ExpenseReportUpdate(BaseModel):
    purpose: Optional[str] = None
    justification: Optional[str] = None
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    project_code: Optional[str] = None
    currency: Optional[str] = None

class ExpenseReportResponse(ExpenseReportBase):
    expense_report_id: int
    employee_id: int
    status: str
    total_amount: Decimal
    duplicate_flag: Optional[bool]
    policy_flags: Optional[str]
    payment_status: Optional[str]
    payment_reference: Optional[str]
    created_at: datetime
    updated_at: datetime
    receipts: List[ReceiptResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class ExpenseApprovalBase(BaseModel):
    status: str
    comments: Optional[str] = None

class ExpenseApprovalResponse(ExpenseApprovalBase):
    approval_id: int
    expense_report_id: int
    approver_id: Optional[int]
    actioned_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)
