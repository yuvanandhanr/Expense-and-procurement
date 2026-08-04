from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Numeric, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    contract_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(100), nullable=False) # MSA, annual_maintenance, software_license, subscription, rate_contract, consultancy
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Draft") # Draft, Active, Expired, Terminated
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_reminder_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor")
    documents: Mapped[List["ContractDocument"]] = relationship("ContractDocument", back_populates="contract", cascade="all, delete-orphan")
    subscription_details: Mapped[Optional["SubscriptionContract"]] = relationship("SubscriptionContract", back_populates="contract", uselist=False, cascade="all, delete-orphan")
    amc_details: Mapped[Optional["AMCContract"]] = relationship("AMCContract", back_populates="contract", uselist=False, cascade="all, delete-orphan")
    rate_details: Mapped[List["RateContract"]] = relationship("RateContract", back_populates="contract", cascade="all, delete-orphan")


class ContractDocument(Base):
    __tablename__ = "contract_documents"

    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("contracts.contract_id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    contract: Mapped["Contract"] = relationship("Contract", back_populates="documents")


class SubscriptionContract(Base):
    __tablename__ = "subscription_contracts"

    subscription_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("contracts.contract_id", ondelete="CASCADE"))
    license_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    billing_frequency: Mapped[str] = mapped_column(String(50), nullable=False) # Monthly, Quarterly, Annually
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    auto_renew: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Relationship
    contract: Mapped["Contract"] = relationship("Contract", back_populates="subscription_details")


class AMCContract(Base):
    __tablename__ = "amc_contracts"

    amc_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("contracts.contract_id", ondelete="CASCADE"))
    coverage_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_sla_hours: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    scheduled_visits_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Relationship
    contract: Mapped["Contract"] = relationship("Contract", back_populates="amc_details")


class RateContract(Base):
    __tablename__ = "rate_contracts"

    rate_contract_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("contracts.contract_id", ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pre_negotiated_unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationship
    contract: Mapped["Contract"] = relationship("Contract", back_populates="rate_details")
