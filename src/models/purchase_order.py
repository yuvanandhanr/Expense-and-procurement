from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    po_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="RESTRICT"))
    rfq_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("request_for_quotations.rfq_id", ondelete="SET NULL"), nullable=True)
    pr_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Draft")
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor")
    rfq: Mapped[Optional["RequestForQuotation"]] = relationship("RequestForQuotation")
    pr: Mapped[Optional["PurchaseRequisition"]] = relationship("PurchaseRequisition")
    department: Mapped[Optional["Department"]] = relationship("Department")
    creator: Mapped[Optional["User"]] = relationship("User")
    items: Mapped[List["PurchaseOrderItem"]] = relationship("PurchaseOrderItem", back_populates="po", cascade="all, delete-orphan")
    approvals: Mapped[List["POApproval"]] = relationship("POApproval", back_populates="po", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    po_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationships
    po: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="items")


class POApproval(Base):
    __tablename__ = "po_approval"

    approval_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="CASCADE"))
    approver_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT"))
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.role_id", ondelete="RESTRICT"))
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Pending")
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    po: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="approvals")
    approver: Mapped["User"] = relationship("User")
    role: Mapped["Role"] = relationship("Role")
