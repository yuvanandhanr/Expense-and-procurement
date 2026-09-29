from typing import Optional, List
from datetime import timezone, datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.schema import FetchedValue
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"

    pr_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for PR"
    )
    pr_number: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="Auto-generated unique PR Number"
    )
    requestor_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, comment="User ID of requestor"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="PR title"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Detailed description of the PR"
    )
    priority: Mapped[Optional[str]] = mapped_column(
        String(50), default="Medium", comment="Priority: Low, Medium, High, Urgent"
    )
    purchase_type: Mapped[Optional[str]] = mapped_column(
        String(50), default="Standard", comment="Purchase Type: Capex, Opex, IT, Standard"
    )
    currency: Mapped[Optional[str]] = mapped_column(
        String(10), default="USD", comment="Transaction currency"
    )
    need_by_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Target date of delivery"
    )
    project_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Associated project identifier"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True, comment="Reference to department"
    )
    cost_center_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("cost_centres.cost_center_id", ondelete="SET NULL"), nullable=True, comment="Reference to cost center"
    )
    justification: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Business justification for the purchase"
    )
    budget_code: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Reference budget code"
    )
    technical_spec_signoff: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="Technical specifications signoff flag"
    )
    technical_spec_signoff_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, comment="User who signed off spec"
    )
    technical_spec_signoff_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Timestamp of tech signoff"
    )
    is_inventory_allocation: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=False, nullable=True, comment="True if satisfied from existing inventory"
    )
    allocated_asset_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("assets.asset_id", ondelete="SET NULL"), nullable=True, comment="Asset ID allocated from inventory"
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50), default="Draft", comment="PR status"
    )
    total_estimated_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=0.00, comment="Sum of estimated item costs"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), comment="PR creation timestamp"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow(), comment="PR modification timestamp"
    )

    # Relationships
    requestor = relationship("User", foreign_keys=[requestor_id])
    department = relationship("Department")
    cost_center = relationship("CostCenter")
    tech_signoff_user = relationship("User", foreign_keys=[technical_spec_signoff_by])
    
    items: Mapped[List["PRItem"]] = relationship(
        "PRItem", back_populates="purchase_requisition", cascade="all, delete-orphan"
    )
    workflows = relationship(
        "ApprovalWorkflow", 
        back_populates="purchase_requisition", 
        cascade="all, delete-orphan"
    )
    history = relationship(
        "WorkflowHistory", back_populates="purchase_requisition", cascade="all, delete-orphan"
    )
    comments = relationship(
        "ApprovalComment", back_populates="purchase_requisition", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "PRAttachment", back_populates="purchase_requisition", cascade="all, delete-orphan"
    )
    reservations = relationship(
        "BudgetReservation", back_populates="purchase_requisition", cascade="all, delete-orphan"
    )

    @property
    def requestor_name(self) -> str:
        if self.requestor:
            return f"{self.requestor.first_name or ''} {self.requestor.last_name or ''}".strip() or "Unknown"
        return "Unknown"


class PRItem(Base):
    __tablename__ = "pr_items"

    pr_item_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for PR Item"
    )
    pr_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="CASCADE"), nullable=True, comment="Associated PR ID"
    )
    category: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Item catalog category"
    )
    item_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Item name"
    )
    specification: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Technical specifications description"
    )
    quantity: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=1, comment="Quantity requested"
    )
    unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, default=0.00, comment="Estimated item unit cost"
    )
    total_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), server_default=FetchedValue(), comment="Quantity * Unit Price"
    )

    purchase_requisition = relationship("PurchaseRequisition", back_populates="items")
