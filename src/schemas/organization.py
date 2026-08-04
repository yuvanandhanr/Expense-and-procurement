from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, FieldValidationInfo, field_validator


class DepartmentBase(BaseModel):
    department_name: str = Field(..., min_length=1, max_length=255)
    department_code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[bool] = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department_code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[bool] = None


class DepartmentSchema(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    department_id: int
    created_at: datetime
    updated_at: datetime


class DesignationBase(BaseModel):
    designation_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[bool] = True


class DesignationCreate(DesignationBase):
    pass


class DesignationUpdate(BaseModel):
    designation_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[bool] = None


class DesignationSchema(DesignationBase):
    model_config = ConfigDict(from_attributes=True)

    designation_id: int
    created_at: datetime
    updated_at: datetime


class CostCenterBase(BaseModel):
    cost_center_name: str = Field(..., min_length=1, max_length=255)
    department_id: Optional[int] = None
    budget_limit: float = Field(..., ge=0.0)
    status: Optional[bool] = True


class CostCenterCreate(CostCenterBase):
    pass


class CostCenterUpdate(BaseModel):
    cost_center_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department_id: Optional[int] = None
    budget_limit: Optional[float] = Field(None, ge=0.0)
    status: Optional[bool] = None


class CostCenterSchema(CostCenterBase):
    model_config = ConfigDict(from_attributes=True)

    cost_center_id: int
    created_at: datetime
    updated_at: datetime


class BudgetCodeBase(BaseModel):
    budget_code: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    annual_budget: float = Field(0.0, ge=0.0)
    available_budget: float = Field(0.0, ge=0.0)
    fiscal_year: str = Field(..., min_length=1, max_length=50)
    status: Optional[str] = "Active"


class BudgetCodeCreate(BudgetCodeBase):
    pass


class BudgetCodeUpdate(BaseModel):
    budget_code: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    annual_budget: Optional[float] = Field(None, ge=0.0)
    available_budget: Optional[float] = Field(None, ge=0.0)
    fiscal_year: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = None


class BudgetCodeSchema(BudgetCodeBase):
    model_config = ConfigDict(from_attributes=True)

    budget_code_id: int
    created_at: datetime
    updated_at: datetime


class OrgSettingsBase(BaseModel):
    org_name: str = Field(..., min_length=1, max_length=255)
    currency: Optional[str] = "USD"
    timezone: Optional[str] = "UTC"
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    approval_thresholds: Optional[dict] = None
    password_policy: Optional[dict] = None
    session_timeout_minutes: Optional[int] = Field(30, ge=1)
    logo_url: Optional[str] = None


class OrgSettingsUpdate(BaseModel):
    org_name: Optional[str] = Field(None, min_length=1, max_length=255)
    currency: Optional[str] = None
    timezone: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    approval_thresholds: Optional[dict] = None
    password_policy: Optional[dict] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=1)
    logo_url: Optional[str] = None


class OrgSettingsSchema(OrgSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    settings_id: int
    created_at: datetime
    updated_at: datetime
