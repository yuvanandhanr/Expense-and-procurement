from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal

# Receipt Schemas
from src.schemas.auth import RoleSchema
import string

class EmployeeBasicSchema(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: List[RoleSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class ReceiptBase(BaseModel):
    merchant_name: Optional[str] = None
    receipt_date: Optional[date] = None
    receipt_number: Optional[str] = None
    category: Optional[str] = None
    verified_amount: Decimal = Field(default=Decimal("0.00"))
    tax: Decimal = Field(default=Decimal("0.00"))
    currency: str = "USD"

class ReceiptCreate(ReceiptBase):
    pass

class ReceiptUpdate(BaseModel):
    # PATCH-style semantics: omitted fields must never overwrite OCR values.
    merchant_name: Optional[str] = None
    receipt_date: Optional[date] = None
    receipt_number: Optional[str] = None
    category: Optional[str] = None
    verified_amount: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    currency: Optional[str] = None

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
    justification: str = Field(..., description="Description / Justification is required")
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    project_code: Optional[str] = None
    currency: str = "USD"
    department_name: Optional[str] = None
    employee_type: Optional[str] = None

    @field_validator('purpose', 'justification')
    @classmethod
    def validate_meaningful_text(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("Must not be empty or whitespace only")
        # Ensure it has letters, not just punctuation or digits
        has_letters = any(c.isalpha() for c in text)
        if not has_letters:
            raise ValueError("Must contain meaningful text/letters, not just numbers or punctuation")
        return text

    @field_validator("justification")
    @classmethod
    def justification_must_not_be_blank(cls, value: str) -> str:
        """Reject whitespace-only descriptions and persist a normalized value."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("Description / Justification is required")
        return normalized

class ExpenseReportCreate(ExpenseReportBase):
    pass

class ExpenseReportUpdate(BaseModel):
    purpose: Optional[str] = None
    justification: Optional[str] = None
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    project_code: Optional[str] = None
    currency: Optional[str] = None

    @field_validator("justification")
    @classmethod
    def justification_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Description / Justification is required")
        return normalized

class ExpenseReportResponse(ExpenseReportBase):
    expense_report_id: int
    employee_id: int
    status: str
    total_amount: Decimal
    duplicate_flag: Optional[bool]
    policy_flags: Optional[str]
    payment_status: Optional[str]
    payment_reference: Optional[str]
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    receipts: List[ReceiptResponse] = []
    employee: Optional[EmployeeBasicSchema] = None
    
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

class ExpenseActionPayload(BaseModel):
    comments: Optional[str] = ""

