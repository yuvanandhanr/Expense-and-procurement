from typing import Optional, List
from datetime import datetime, date
from sqlalchemy import BigInteger, String, Text, DateTime, Date, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Asset(Base):
    __tablename__ = "assets"

    asset_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    asset_tag: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("asset_categories.category_id", ondelete="SET NULL"), nullable=True)
    po_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="SET NULL"), nullable=True)
    vendor_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="SET NULL"), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True)
    assigned_employee_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    warranty_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amc_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Available") # Available, Assigned, Under Maintenance, Disposed, Returned, Lost
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    category: Mapped[Optional["AssetCategory"]] = relationship("AssetCategory")
    po: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor")
    department: Mapped[Optional["Department"]] = relationship("Department")
    assigned_employee: Mapped[Optional["User"]] = relationship("User")
    assignments: Mapped[List["AssetAssignment"]] = relationship("AssetAssignment", back_populates="asset", cascade="all, delete-orphan")
    history: Mapped[List["AssetHistory"]] = relationship("AssetHistory", back_populates="asset", cascade="all, delete-orphan")
    documents: Mapped[List["AssetDocument"]] = relationship("AssetDocument", back_populates="asset", cascade="all, delete-orphan")
    incidents: Mapped[List["AssetIncident"]] = relationship("AssetIncident", back_populates="asset", cascade="all, delete-orphan")


class AssetAssignment(Base):
    __tablename__ = "asset_assignments"

    assignment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.asset_id", ondelete="CASCADE"))
    assigned_to: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    assigned_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # Active, Returned, Transferred
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="assignments")
    employee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])
    assigner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by])


class AssetHistory(Base):
    __tablename__ = "asset_history"

    history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.asset_id", ondelete="CASCADE"))
    action_type: Mapped[str] = mapped_column(String(100), nullable=False) # Registration, Assignment, Transfer, Return, Maintenance, Disposal
    action_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="history")
    actor: Mapped[Optional["User"]] = relationship("User")


class AssetDocument(Base):
    __tablename__ = "asset_documents"

    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.asset_id", ondelete="CASCADE"))
    document_type: Mapped[str] = mapped_column(String(100), nullable=False) # Invoice, Warranty, Certificate, Manual
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    asset: Mapped["Asset"] = relationship("Asset", back_populates="documents")


class AssetIncident(Base):
    __tablename__ = "asset_incidents"

    incident_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.asset_id", ondelete="CASCADE"))
    reporter_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    incident_date: Mapped[date] = mapped_column(Date, default=date.today)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False) # Damage, Loss, Theft
    status: Mapped[str] = mapped_column(String(50), default="Reported") # Reported, Inspection Pending, Repair, Replacement, Closed
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    physical_inspection_done: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default='false')
    linked_pr_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="incidents")
    reporter: Mapped[Optional["User"]] = relationship("User")
    linked_pr = relationship("PurchaseRequisition", foreign_keys=[linked_pr_id])
