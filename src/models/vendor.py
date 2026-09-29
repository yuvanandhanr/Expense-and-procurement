from typing import Optional, List
from datetime import timezone, datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gst_vat_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tax_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default="USD")
    preferred_vendor: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Active")
    blacklist_status: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mfa_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_terms: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bank_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    contacts: Mapped[List["VendorContact"]] = relationship("VendorContact", back_populates="vendor", cascade="all, delete-orphan")
    documents: Mapped[List["VendorDocument"]] = relationship("VendorDocument", back_populates="vendor", cascade="all, delete-orphan")
    categories: Mapped[List["VendorCategory"]] = relationship("VendorCategory", back_populates="vendor", cascade="all, delete-orphan")
    performance: Mapped[Optional["VendorPerformance"]] = relationship("VendorPerformance", back_populates="vendor", uselist=False, cascade="all, delete-orphan")
    blacklist_records: Mapped[List["VendorBlacklist"]] = relationship("VendorBlacklist", back_populates="vendor", cascade="all, delete-orphan")


class VendorContact(Base):
    __tablename__ = "vendor_contacts"

    contact_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationship
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="contacts")


class VendorDocument(Base):
    __tablename__ = "vendor_documents"

    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationship
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="documents")


class VendorCategory(Base):
    __tablename__ = "vendor_categories"

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationship
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="categories")


class VendorPerformance(Base):
    __tablename__ = "vendor_performance"

    performance_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    delivery_performance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100.00)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100.00)
    response_time: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100.00)
    contract_compliance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100.00)
    purchase_volume: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    avg_lead_time_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.00)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=5.00)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationship
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="performance")


class VendorBlacklist(Base):
    __tablename__ = "vendor_blacklist"

    blacklist_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    blacklisted_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="blacklist_records")
