from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PRItemBase(BaseModel):
    category: str = Field(..., description="Catalog category, e.g. IT, Office Supplies")
    item_name: str = Field(..., description="Name of the item requested")
    specification: Optional[str] = Field(None, description="Technical specifications description")
    quantity: int = Field(1, gt=0, description="Quantity requested")
    unit_price: Optional[Decimal] = Field(0.00, ge=0, description="Estimated unit price cost")


class PRItemCreate(PRItemBase):
    pass


class PRItemUpdate(BaseModel):
    category: Optional[str] = None
    item_name: Optional[str] = None
    specification: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, gt=0)


class PRItemSchema(PRItemBase):
    model_config = ConfigDict(from_attributes=True)

    pr_item_id: int
    pr_id: Optional[int] = None
    total_price: Optional[Decimal] = None


class PRBase(BaseModel):
    title: str = Field(..., description="Brief summary of request")
    justification: str = Field(..., description="Business need validation")
    department_id: Optional[int] = Field(None, description="Department code")
    cost_center_id: Optional[int] = Field(None, description="Cost center code")
    budget_code: Optional[str] = Field(None, description="Budget identifier")
    priority: Optional[str] = Field("Medium", description="Low, Medium, High, Urgent")
    purchase_type: Optional[str] = Field("Standard", description="IT, Capex, Opex, Standard")
    need_by_date: Optional[datetime] = None
    project_code: Optional[str] = None


class PRCreate(PRBase):
    items: List[PRItemCreate] = Field(..., min_length=1, description="List of items requested")


class PRUpdate(BaseModel):
    title: Optional[str] = None
    justification: Optional[str] = None
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    budget_code: Optional[str] = None
    priority: Optional[str] = None
    purchase_type: Optional[str] = None
    need_by_date: Optional[datetime] = None
    project_code: Optional[str] = None
    items: Optional[List[PRItemCreate]] = None

class PRAllocateInventoryRequest(BaseModel):
    asset_id: int = Field(..., description="ID of the asset to allocate")


class PRSchema(PRBase):
    model_config = ConfigDict(from_attributes=True)

    pr_id: int
    pr_number: str
    requestor_id: Optional[int] = None
    requestor_name: Optional[str] = None
    status: str
    total_estimated_amount: Decimal
    technical_spec_signoff: Optional[bool] = None
    technical_spec_signoff_by: Optional[int] = None
    technical_spec_signoff_at: Optional[datetime] = None
    is_inventory_allocation: Optional[bool] = False
    allocated_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[PRItemSchema] = []
