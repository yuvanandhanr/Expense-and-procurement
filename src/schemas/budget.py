from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class BudgetAllocationBase(BaseModel):
    budget_code_id: int = Field(..., description="Foreign key referencing budget codes table")
    allocated_amount: Decimal = Field(..., gt=0, description="Annual allocation sum limit")
    fiscal_year: str = Field(..., description="Target fiscal year, e.g. FY2026")
    status: Optional[str] = Field("Active", description="Active or Inactive")


class BudgetAllocationCreate(BudgetAllocationBase):
    pass


class BudgetAllocationSchema(BudgetAllocationBase):
    model_config = ConfigDict(from_attributes=True)

    allocation_id: int
    spent_amount: Decimal
    reserved_amount: Decimal
    created_at: datetime
    updated_at: datetime


class BudgetReservationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reservation_id: int
    pr_id: int
    budget_code_id: int
    reserved_amount: Decimal
    status: str
    created_at: datetime
    released_at: Optional[datetime] = None
