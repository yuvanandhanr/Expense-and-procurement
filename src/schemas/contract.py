from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class ContractDocumentCreate(BaseModel):
    file_name: str
    file_path: str


class ContractDocumentSchema(ContractDocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    contract_id: int
    uploaded_at: datetime


class SubscriptionContractCreate(BaseModel):
    license_count: int
    billing_frequency: str
    unit_price: Decimal
    auto_renew: Optional[bool] = False


class SubscriptionContractSchema(SubscriptionContractCreate):
    model_config = ConfigDict(from_attributes=True)

    subscription_id: int
    contract_id: int


class AMCContractCreate(BaseModel):
    coverage_details: Optional[str] = None
    response_sla_hours: Optional[int] = None
    scheduled_visits_count: Optional[int] = None


class AMCContractSchema(AMCContractCreate):
    model_config = ConfigDict(from_attributes=True)

    amc_id: int
    contract_id: int


class RateContractCreate(BaseModel):
    item_name: str
    specification: Optional[str] = None
    pre_negotiated_unit_price: Decimal


class RateContractSchema(RateContractCreate):
    model_config = ConfigDict(from_attributes=True)

    rate_contract_id: int
    contract_id: int


class ContractCreate(BaseModel):
    contract_number: str
    vendor_id: int
    title: str
    contract_type: str # MSA, annual_maintenance, software_license, subscription, rate_contract, consultancy
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    expiry_reminder_date: Optional[date] = None
    subscription_details: Optional[SubscriptionContractCreate] = None
    amc_details: Optional[AMCContractCreate] = None
    rate_details: Optional[List[RateContractCreate]] = []


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    expiry_reminder_date: Optional[date] = None


class ContractSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contract_id: int
    contract_number: str
    vendor_id: int
    title: str
    contract_type: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    expiry_reminder_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    documents: List[ContractDocumentSchema] = []
    subscription_details: Optional[SubscriptionContractSchema] = None
    amc_details: Optional[AMCContractSchema] = None
    rate_details: List[RateContractSchema] = []
