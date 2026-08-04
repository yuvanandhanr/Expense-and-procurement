from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class ThreeWayMatchingCreate(BaseModel):
    invoice_id: int
    po_id: Optional[int] = None
    grn_id: Optional[int] = None


class ThreeWayMatchingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matching_id: int
    invoice_id: int
    po_id: Optional[int] = None
    grn_id: Optional[int] = None
    item_match_passed: bool
    quantity_match_passed: bool
    price_match_passed: bool
    tax_match_passed: bool
    currency_match_passed: bool
    total_amount_match_passed: bool
    variance_amount: Decimal
    match_result: str
    inspected_at: datetime
